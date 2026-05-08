import json
import logging
import re
import sys
import time
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Annotated, Any

from agent_framework import (
    Agent,
    AgentSession,
    MCPStdioTool,
    MCPStreamableHTTPTool,
    Message,
)
from agent_framework_openai import OpenAIChatCompletionClient
from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import (
    FunctionTool as ProjectsFunctionTool,
    MCPTool as ProjectsMCPTool,
    PromptAgentDefinition,
)
from azure.identity.aio import DefaultAzureCredential

from app.agent.prompts import SYSTEM_PROMPT
from app.config import settings
from app.services.school_data import search_school

logger = logging.getLogger("geo_agent")

# Pattern to strip Bing grounding citation tags like citeturn0search0
_CITE_TAG_RE = re.compile(r"\bciteturn\d+search\d+\b")
_CITE_HOLDBACK = 25  # max chars to buffer for split citation tags

_backend_dir = Path(__file__).resolve().parent.parent.parent
_python_exe = sys.executable
_base_env = {"PYTHONPATH": str(_backend_dir), "PATH": sys.prefix}

_SESSION_MAX_AGE = 30 * 60  # 30 minutes
_SESSION_CLEANUP_INTERVAL = 5 * 60  # check every 5 minutes


# ---------------------------------------------------------------------------
# Local-only function tool: school detail lookup
# ---------------------------------------------------------------------------

def lookup_school_details(
    school_name: Annotated[
        str,
        "The name of the school to look up (e.g. 'St Hilda's Primary School')",
    ],
) -> str:
    """Look up detailed information about a Singapore school by name.

    Returns general info, subjects offered, CCAs, distinctive programmes,
    and more. Uses fuzzy matching to handle typos and abbreviations.
    """
    result = search_school(school_name)
    if result is None:
        return json.dumps(
            {
                "error": f"No school found matching '{school_name}'. Try a more specific name."
            }
        )
    return json.dumps(result, default=str)


# ---------------------------------------------------------------------------
# Strategy A: in-process agent via Chat Completions (dev / local)
# ---------------------------------------------------------------------------


class _ChatCompletionStrategy:
    """Runs the agent in-process using OpenAI Chat Completions over the
    Foundry project's OpenAI-compatible endpoint. Tools (MCP servers + the
    local school helper) execute client-side.

    Chat Completions is stateless on every turn — the framework sends the
    full conversation history including assistant tool_calls — which avoids
    the broken response-id chaining we saw on Foundry's Responses endpoint.
    """

    def __init__(self) -> None:
        self._agent: Agent | None = None
        self._onemap_mcp: MCPStdioTool | MCPStreamableHTTPTool | None = None
        self._ura_mcp: MCPStdioTool | MCPStreamableHTTPTool | None = None
        self._moe_mcp: MCPStdioTool | MCPStreamableHTTPTool | None = None
        self._project_client: AIProjectClient | None = None
        self._sessions: dict[str, tuple[AgentSession, float]] = {}
        self._last_cleanup = 0.0

    async def initialize(self) -> None:
        # OneMap MCP
        if settings.onemap_mcp_url:
            logger.info("OneMap MCP: HTTP → %s", settings.onemap_mcp_url)
            self._onemap_mcp = MCPStreamableHTTPTool(
                name="onemap",
                url=settings.onemap_mcp_url,
                tool_name_prefix="onemap_",
            )
        else:
            logger.info("OneMap MCP: local stdio")
            self._onemap_mcp = MCPStdioTool(
                name="onemap",
                command=_python_exe,
                args=["-m", "mcp_servers.onemap"],
                env={
                    **_base_env,
                    "ONEMAP_EMAIL": settings.onemap_email,
                    "ONEMAP_PASSWORD": settings.onemap_password,
                },
                tool_name_prefix="onemap_",
            )

        # URA MCP
        if settings.ura_mcp_url:
            logger.info("URA MCP: HTTP → %s", settings.ura_mcp_url)
            self._ura_mcp = MCPStreamableHTTPTool(
                name="ura",
                url=settings.ura_mcp_url,
                tool_name_prefix="ura_",
            )
        else:
            logger.info("URA MCP: local stdio")
            self._ura_mcp = MCPStdioTool(
                name="ura",
                command=_python_exe,
                args=["-m", "mcp_servers.ura"],
                env={
                    **_base_env,
                    "URA_ACCESS_KEY": settings.ura_access_key,
                },
                tool_name_prefix="ura_",
            )

        # MOE MCP
        if settings.moe_mcp_url:
            logger.info("MOE MCP: HTTP → %s", settings.moe_mcp_url)
            self._moe_mcp = MCPStreamableHTTPTool(
                name="moe",
                url=settings.moe_mcp_url,
                tool_name_prefix="moe_",
            )
        else:
            logger.info("MOE MCP: local stdio")
            self._moe_mcp = MCPStdioTool(
                name="moe",
                command=_python_exe,
                args=["-m", "mcp_servers.moe"],
                env=_base_env,
                tool_name_prefix="moe_",
            )

        tools: list[Any] = [
            self._onemap_mcp,
            self._ura_mcp,
            self._moe_mcp,
            lookup_school_details,
        ]
        logger.info("School detail lookup tool enabled (local JSON)")

        self._project_client = AIProjectClient(
            endpoint=settings.azure_ai_project_endpoint,
            credential=DefaultAzureCredential(),
        )
        client = OpenAIChatCompletionClient(
            model=settings.model_deployment_name,
            async_client=self._project_client.get_openai_client(),
        )
        logger.info(
            "Chat client: OpenAI Chat Completions via Foundry project (model=%s)",
            settings.model_deployment_name,
        )

        self._agent = Agent(
            client=client,
            instructions=SYSTEM_PROMPT,
            name="GeoAgent",
            description="Geospatial AI Agent for Singapore spatial data",
            tools=tools,
        )

    async def cleanup(self) -> None:
        for mcp_tool in (self._onemap_mcp, self._ura_mcp, self._moe_mcp):
            if mcp_tool is not None:
                try:
                    await mcp_tool.close()
                except Exception:
                    logger.debug(
                        "Error closing MCP tool %s",
                        getattr(mcp_tool, "name", "?"),
                        exc_info=True,
                    )
        if self._project_client is not None:
            try:
                await self._project_client.close()
            except Exception:
                logger.debug("Error closing AIProjectClient", exc_info=True)
        self._agent = None
        self._onemap_mcp = None
        self._ura_mcp = None
        self._moe_mcp = None
        self._project_client = None
        self._sessions.clear()

    def _evict_stale_sessions(self) -> None:
        now = time.monotonic()
        if now - self._last_cleanup < _SESSION_CLEANUP_INTERVAL:
            return
        self._last_cleanup = now
        cutoff = now - _SESSION_MAX_AGE
        stale = [sid for sid, (_, ts) in self._sessions.items() if ts < cutoff]
        for sid in stale:
            del self._sessions[sid]
        if stale:
            logger.info(
                "Evicted %d stale sessions (%d remaining)",
                len(stale),
                len(self._sessions),
            )

    async def run_stream(
        self, session_id: str, user_message: str
    ) -> AsyncIterator[dict]:
        if not self._agent:
            raise RuntimeError("Agent not initialized")

        self._evict_stale_sessions()

        now = time.monotonic()
        if session_id in self._sessions:
            session, _ = self._sessions[session_id]
        else:
            session = AgentSession(session_id=session_id)
        self._sessions[session_id] = (session, now)

        logger.info("[%s] User: %s", session_id[:8], user_message[:200])

        stream = self._agent.run(
            Message("user", [user_message]),
            session=session,
            stream=True,
        )

        pending_calls: dict[str, dict] = {}
        web_search_emitted = False
        web_search_citations: list[dict] = []
        cite_buffer = ""

        async for update in stream:
            if not update.contents:
                continue

            for content in update.contents:
                if content.type == "function_call":
                    call_id = content.call_id or ""
                    name = content.name or "unknown"
                    arg_chunk = content.arguments or ""

                    if call_id not in pending_calls:
                        pending_calls[call_id] = {"name": name, "args_parts": []}
                        logger.info("[%s] Tool call: %s", session_id[:8], name)
                        yield {
                            "type": "tool_call",
                            "name": name,
                            "arguments": {},
                            "status": "executing",
                            "result": None,
                        }

                    if isinstance(arg_chunk, str) and arg_chunk:
                        pending_calls[call_id]["args_parts"].append(arg_chunk)

                elif content.type == "function_result":
                    call_id = content.call_id or ""
                    call_info = pending_calls.pop(call_id, None)
                    name = (
                        (call_info["name"] if call_info else None)
                        or content.name
                        or "unknown"
                    )

                    args: dict[str, Any] = {}
                    if call_info and call_info["args_parts"]:
                        raw = "".join(call_info["args_parts"])
                        try:
                            args = json.loads(raw)
                        except Exception:
                            args = {"raw": raw}

                    raw_result = content.result
                    result_str = ""
                    try:
                        if raw_result is not None:
                            result_str = json.dumps(
                                raw_result, default=str, ensure_ascii=False
                            )
                        else:
                            result_str = str(getattr(content, "text", "") or "")
                    except Exception:
                        result_str = str(raw_result) if raw_result else ""

                    display_result = result_str
                    if len(display_result) > 2000:
                        display_result = display_result[:2000] + "... (truncated)"

                    logger.info(
                        "[%s] Tool result: %s len=%d",
                        session_id[:8],
                        name,
                        len(result_str),
                    )
                    yield {
                        "type": "tool_call",
                        "name": name,
                        "arguments": args,
                        "status": "completed",
                        "result": display_result,
                        "full_result": result_str,
                    }

                elif content.type == "text":
                    annotations = getattr(content, "annotations", None) or []
                    for ann in annotations:
                        ann_type = (
                            getattr(ann, "type", None)
                            if not isinstance(ann, dict)
                            else ann.get("type")
                        )
                        if ann_type == "citation":
                            title = (
                                getattr(ann, "title", None)
                                if not isinstance(ann, dict)
                                else ann.get("title")
                            ) or ""
                            url = (
                                getattr(ann, "url", None)
                                if not isinstance(ann, dict)
                                else ann.get("url")
                            ) or ""
                            if not web_search_emitted:
                                web_search_emitted = True
                                logger.info(
                                    "[%s] Tool call: bing_web_search (server-side)",
                                    session_id[:8],
                                )
                                yield {
                                    "type": "tool_call",
                                    "name": "bing_web_search",
                                    "arguments": {},
                                    "status": "executing",
                                    "result": None,
                                }
                            if url:
                                web_search_citations.append(
                                    {"title": title, "url": url}
                                )

                    delta = content.text or ""
                    if delta:
                        cite_buffer += delta
                        cite_buffer = _CITE_TAG_RE.sub("", cite_buffer)
                        if len(cite_buffer) > _CITE_HOLDBACK:
                            safe = cite_buffer[:-_CITE_HOLDBACK]
                            cite_buffer = cite_buffer[-_CITE_HOLDBACK:]
                            if safe:
                                yield {"type": "delta", "text": safe}

        if cite_buffer:
            cite_buffer = _CITE_TAG_RE.sub("", cite_buffer)
            if cite_buffer:
                yield {"type": "delta", "text": cite_buffer}

        if web_search_emitted:
            sources = (
                "\n".join(
                    f"- [{c['title']}]({c['url']})" for c in web_search_citations
                )
                if web_search_citations
                else "Search completed"
            )
            logger.info(
                "[%s] Bing web search completed, %d citations",
                session_id[:8],
                len(web_search_citations),
            )
            yield {
                "type": "tool_call",
                "name": "bing_web_search",
                "arguments": {},
                "status": "completed",
                "result": sources,
            }

        logger.info("[%s] Stream complete", session_id[:8])


# ---------------------------------------------------------------------------
# Strategy B: Foundry Agent Service (prod / Container Apps)
# ---------------------------------------------------------------------------

# JSON schema for the local school-details function tool, sent to Foundry so
# the model knows how to call it. The actual execution is performed by this
# backend (handle_required_action below).
_LOOKUP_SCHOOL_DETAILS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "school_name": {
            "type": "string",
            "description": (
                "The name of the school to look up "
                "(e.g. 'St Hilda's Primary School')"
            ),
        },
    },
    "required": ["school_name"],
    "additionalProperties": False,
}


class _FoundryAgentServiceStrategy:
    """Runs the agent against an Azure AI Foundry **Prompt Agent** (the new
    declarative versioned agent shown under "Agents" in the Foundry portal,
    not the legacy threads/runs agents).

    On startup, upserts a prompt agent named ``settings.foundry_agent_name``
    via ``AIProjectClient.beta.agents.create_version()`` with a
    ``PromptAgentDefinition`` that registers:

    - the three deployed MCP container apps as ``MCPTool`` entries
      (``require_approval="never"`` → executed server-side by Foundry)
    - the local ``lookup_school_details`` helper as a ``FunctionTool``
      (executed in this backend during the Responses API loop)

    Invocation goes through the agent's OpenAI-compatible Responses endpoint
    obtained via ``project_client.get_openai_client(agent_name=...)`` (which
    requires ``allow_preview=True``). We send the **full conversation history
    on every turn** (``store=False``) so we don't depend on Foundry's
    server-side response chaining, which has bitten us before.
    """

    def __init__(self) -> None:
        self._project_client: AIProjectClient | None = None
        self._credential: DefaultAzureCredential | None = None
        self._openai_client: Any = None  # AsyncOpenAI rooted at agent endpoint
        # Per-session conversation history (Responses API "input" item list).
        # session_id -> (input_items, last_used_monotonic)
        self._sessions: dict[str, tuple[list[dict[str, Any]], float]] = {}
        self._last_cleanup = 0.0

    async def initialize(self) -> None:
        # Validate prereqs upfront so prod misconfig surfaces immediately.
        missing = [
            name
            for name, value in (
                ("ONEMAP_MCP_URL", settings.onemap_mcp_url),
                ("URA_MCP_URL", settings.ura_mcp_url),
                ("MOE_MCP_URL", settings.moe_mcp_url),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(
                "AGENT_MODE=foundry_agent_service requires the following "
                f"environment variables to be set: {', '.join(missing)}"
            )
        if not settings.azure_ai_project_endpoint:
            raise RuntimeError(
                "AGENT_MODE=foundry_agent_service requires "
                "AZURE_AI_PROJECT_ENDPOINT to be set."
            )

        self._credential = DefaultAzureCredential()
        # `allow_preview=True` is required to use the new prompt-agent surface
        # (`beta.agents`) and the agent-scoped OpenAI endpoint
        # (`get_openai_client(agent_name=...)`).
        self._project_client = AIProjectClient(
            endpoint=settings.azure_ai_project_endpoint,
            credential=self._credential,
            allow_preview=True,
        )

        # Build the prompt agent definition (model + instructions + tools).
        # Note: in this API, MCPTool carries `require_approval` directly on
        # the tool definition itself — there is no separate ToolResources.
        tools_list = [
            ProjectsMCPTool(
                server_label="onemap",
                server_url=settings.onemap_mcp_url,
                require_approval="never",
            ),
            ProjectsMCPTool(
                server_label="ura",
                server_url=settings.ura_mcp_url,
                require_approval="never",
            ),
            ProjectsMCPTool(
                server_label="moe",
                server_url=settings.moe_mcp_url,
                require_approval="never",
            ),
            ProjectsFunctionTool(
                name="lookup_school_details",
                description=(
                    "Look up detailed information about a Singapore school by "
                    "name. Returns general info, subjects offered, CCAs, "
                    "distinctive programmes, and more."
                ),
                parameters=_LOOKUP_SCHOOL_DETAILS_SCHEMA,
                strict=True,
            ),
        ]

        definition = PromptAgentDefinition(
            model=settings.model_deployment_name,
            instructions=SYSTEM_PROMPT,
            tools=tools_list,
        )

        # Upsert: every call to `create_version()` produces a new immutable
        # version. If the agent name doesn't exist yet, the first version is
        # created implicitly. We don't try to dedupe on definition equality —
        # cheaper to let the SDK manage versions.
        try:
            new_version = await self._project_client.agents.create_version(
                agent_name=settings.foundry_agent_name,
                definition=definition,
                description="Geospatial AI Agent for Singapore spatial data",
            )
            logger.info(
                "Foundry prompt agent '%s' upserted: version=%s, model=%s",
                settings.foundry_agent_name,
                getattr(new_version, "version", "?"),
                settings.model_deployment_name,
            )
        except Exception:
            logger.exception(
                "Failed to upsert Foundry prompt agent '%s'",
                settings.foundry_agent_name,
            )
            raise

        # OpenAI client routed at the agent's endpoint:
        # `<endpoint>/agents/<name>/endpoint/protocols/openai`. Calls to
        # `responses.create()` on this client invoke the agent (with its
        # configured model + tools + instructions) directly.
        self._openai_client = self._project_client.get_openai_client(
            agent_name=settings.foundry_agent_name
        )

        logger.info(
            "Registered MCP tools on Foundry prompt agent: "
            "onemap=%s ura=%s moe=%s",
            settings.onemap_mcp_url,
            settings.ura_mcp_url,
            settings.moe_mcp_url,
        )

    async def cleanup(self) -> None:
        # Per design decision: do NOT delete the Foundry agent on shutdown —
        # the next startup just creates a new version on top.
        if self._openai_client is not None:
            try:
                await self._openai_client.close()
            except Exception:
                logger.debug("Error closing OpenAI client", exc_info=True)
        if self._project_client is not None:
            try:
                await self._project_client.close()
            except Exception:
                logger.debug("Error closing AIProjectClient", exc_info=True)
        if self._credential is not None:
            try:
                await self._credential.close()
            except Exception:
                logger.debug("Error closing credential", exc_info=True)
        self._openai_client = None
        self._project_client = None
        self._credential = None
        self._sessions.clear()

    def _evict_stale_sessions(self) -> None:
        now = time.monotonic()
        if now - self._last_cleanup < _SESSION_CLEANUP_INTERVAL:
            return
        self._last_cleanup = now
        cutoff = now - _SESSION_MAX_AGE
        stale = [sid for sid, (_, ts) in self._sessions.items() if ts < cutoff]
        for sid in stale:
            del self._sessions[sid]
        if stale:
            logger.info(
                "Evicted %d stale Foundry sessions (%d remaining)",
                len(stale),
                len(self._sessions),
            )

    def _get_input_history(self, session_id: str) -> list[dict[str, Any]]:
        if session_id in self._sessions:
            history, _ = self._sessions[session_id]
            return history
        history = []
        self._sessions[session_id] = (history, time.monotonic())
        return history

    def _touch_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            history, _ = self._sessions[session_id]
            self._sessions[session_id] = (history, time.monotonic())

    async def run_stream(
        self, session_id: str, user_message: str
    ) -> AsyncIterator[dict]:
        if not self._openai_client:
            raise RuntimeError("Foundry prompt agent not initialized")

        self._evict_stale_sessions()
        history = self._get_input_history(session_id)
        history.append(
            {
                "role": "user",
                "content": [{"type": "input_text", "text": user_message}],
            }
        )
        self._touch_session(session_id)

        logger.info(
            "[%s] User (history_len=%d): %s",
            session_id[:8],
            len(history),
            user_message[:200],
        )

        cite_buffer = ""
        # Loop: keep calling the Responses API until the agent stops asking
        # for local function-tool execution. MCP tool calls are handled by
        # Foundry server-side, so they don't drive the loop.
        for hop in range(8):  # safety bound
            # Per-hop streaming state.
            # output_index -> dict tracking item being built (function_call /
            # mcp_call). For function_call we accumulate name + arguments + call_id.
            pending_items: dict[int, dict[str, Any]] = {}
            # Items to append to history after this hop completes.
            hop_history_additions: list[dict[str, Any]] = []
            # Local function calls that need execution before the next hop.
            pending_function_calls: list[dict[str, Any]] = []

            try:
                stream = await self._openai_client.responses.create(
                    model=settings.model_deployment_name,
                    input=history,
                    stream=True,
                    store=False,
                )
            except Exception:
                logger.exception(
                    "[%s] responses.create() failed (hop=%d)",
                    session_id[:8],
                    hop,
                )
                raise

            async for event in stream:
                ev_type = getattr(event, "type", None)

                # Text deltas → stream to UI (with citation-tag scrubbing).
                if ev_type == "response.output_text.delta":
                    delta = getattr(event, "delta", "") or ""
                    if not delta:
                        continue
                    cite_buffer += delta
                    cite_buffer = _CITE_TAG_RE.sub("", cite_buffer)
                    if len(cite_buffer) > _CITE_HOLDBACK:
                        safe = cite_buffer[:-_CITE_HOLDBACK]
                        cite_buffer = cite_buffer[-_CITE_HOLDBACK:]
                        if safe:
                            yield {"type": "delta", "text": safe}
                    continue

                # New output item appears (function_call / mcp_call / message).
                if ev_type == "response.output_item.added":
                    item = getattr(event, "item", None)
                    output_index = getattr(event, "output_index", None)
                    item_type = getattr(item, "type", None)
                    if output_index is None or item is None:
                        continue
                    if item_type == "function_call":
                        name = getattr(item, "name", None) or ""
                        call_id = getattr(item, "call_id", None) or ""
                        pending_items[output_index] = {
                            "type": "function_call",
                            "name": name,
                            "call_id": call_id,
                            "arguments": "",
                        }
                        logger.info(
                            "[%s] Local function call started: %s (call_id=%s)",
                            session_id[:8],
                            name,
                            call_id,
                        )
                        yield {
                            "type": "tool_call",
                            "name": name,
                            "arguments": {},
                            "status": "executing",
                            "result": None,
                        }
                    elif item_type == "mcp_call":
                        server_label = getattr(item, "server_label", None) or ""
                        tool_name = getattr(item, "name", None) or ""
                        display_name = (
                            f"{server_label}_{tool_name}"
                            if server_label and tool_name
                            else (tool_name or server_label or "mcp")
                        )
                        pending_items[output_index] = {
                            "type": "mcp_call",
                            "name": display_name,
                            "server_label": server_label,
                            "tool_name": tool_name,
                            "arguments": "",
                        }
                        logger.info(
                            "[%s] MCP call started: %s",
                            session_id[:8],
                            display_name,
                        )
                        yield {
                            "type": "tool_call",
                            "name": display_name,
                            "arguments": {},
                            "status": "executing",
                            "result": None,
                        }
                    continue

                # Streamed function_call argument deltas.
                if ev_type == "response.function_call_arguments.delta":
                    output_index = getattr(event, "output_index", None)
                    delta = getattr(event, "delta", "") or ""
                    if output_index in pending_items and delta:
                        pending_items[output_index]["arguments"] += delta
                    continue

                # Streamed MCP-call argument deltas.
                if ev_type == "response.mcp_call_arguments.delta":
                    output_index = getattr(event, "output_index", None)
                    delta = getattr(event, "delta", "") or ""
                    if output_index in pending_items and delta:
                        pending_items[output_index]["arguments"] += delta
                    continue

                # An output item finished — record it and (for MCP) emit
                # completed event.
                if ev_type == "response.output_item.done":
                    item = getattr(event, "item", None)
                    output_index = getattr(event, "output_index", None)
                    item_type = getattr(item, "type", None)
                    if item is None or output_index is None:
                        continue

                    pending = pending_items.pop(output_index, None)

                    if item_type == "function_call":
                        # Append the assistant function_call to history (full
                        # item as-dict so the next responses.create() can see it).
                        item_dict = _to_dict(item)
                        hop_history_additions.append(item_dict)
                        # Queue for local execution.
                        pending_function_calls.append(
                            {
                                "call_id": item_dict.get("call_id") or item_dict.get("id"),
                                "name": item_dict.get("name", ""),
                                "arguments": item_dict.get("arguments", "{}"),
                            }
                        )
                    elif item_type == "mcp_call":
                        # Foundry already executed this server-side; emit
                        # completed event and stash the output in history so
                        # subsequent hops have context.
                        item_dict = _to_dict(item)
                        hop_history_additions.append(item_dict)
                        output_str = (
                            item_dict.get("output")
                            or getattr(item, "output", "")
                            or ""
                        )
                        display_name = (
                            pending["name"] if pending else item_dict.get("name", "mcp")
                        )
                        try:
                            args_obj = json.loads(item_dict.get("arguments", "{}"))
                        except Exception:
                            args_obj = {"raw": item_dict.get("arguments", "")}
                        display = output_str
                        if len(display) > 2000:
                            display = display[:2000] + "... (truncated)"
                        logger.info(
                            "[%s] MCP call completed: %s len=%d",
                            session_id[:8],
                            display_name,
                            len(output_str),
                        )
                        yield {
                            "type": "tool_call",
                            "name": display_name,
                            "arguments": args_obj,
                            "status": "completed",
                            "result": display,
                            "full_result": output_str,
                        }
                    elif item_type == "message":
                        # Final assistant message — stash so future hops have
                        # the conversation context.
                        hop_history_additions.append(_to_dict(item))
                    else:
                        # Unknown item types (reasoning, etc.) — just stash.
                        hop_history_additions.append(_to_dict(item))
                    continue

                # Surface server-side errors as exceptions so the websocket
                # router converts them to error frames.
                if ev_type == "error" or ev_type == "response.error":
                    err = getattr(event, "error", None) or event
                    logger.error(
                        "[%s] Responses stream error: %r", session_id[:8], err
                    )
                    raise RuntimeError(f"Foundry agent run failed: {err!r}")

                # Anything else (response.created, response.in_progress,
                # response.output_text.done, response.completed, etc.) is
                # informational — ignore.

            # End of one streaming response. Append accumulated assistant
            # outputs to the running history.
            history.extend(hop_history_additions)

            if not pending_function_calls:
                break

            # Execute the local function tool(s) and append outputs.
            for fc in pending_function_calls:
                call_id = fc.get("call_id") or ""
                name = fc.get("name") or ""
                raw_args = fc.get("arguments") or "{}"
                try:
                    args_obj = (
                        json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                    )
                except Exception:
                    args_obj = {"raw": raw_args}

                logger.info(
                    "[%s] Executing local function tool: %s args=%s",
                    session_id[:8],
                    name,
                    args_obj,
                )

                if name == "lookup_school_details":
                    output = lookup_school_details(
                        school_name=args_obj.get("school_name", "")
                    )
                else:
                    output = json.dumps(
                        {"error": f"Unknown local tool: {name!r}"}
                    )

                history.append(
                    {
                        "type": "function_call_output",
                        "call_id": call_id,
                        "output": output,
                    }
                )

                display = output
                if len(display) > 2000:
                    display = display[:2000] + "... (truncated)"
                yield {
                    "type": "tool_call",
                    "name": name,
                    "arguments": args_obj,
                    "status": "completed",
                    "result": display,
                    "full_result": output,
                }

            self._touch_session(session_id)
        else:
            logger.warning(
                "[%s] Hit hop limit (8) — function-call loop did not terminate",
                session_id[:8],
            )

        # Flush any held-back text after citation scrubbing.
        if cite_buffer:
            cite_buffer = _CITE_TAG_RE.sub("", cite_buffer)
            if cite_buffer:
                yield {"type": "delta", "text": cite_buffer}

        logger.info("[%s] Stream complete", session_id[:8])


def _to_dict(item: Any) -> dict[str, Any]:
    """Best-effort conversion of an SDK output item into a JSON-serialisable
    dict suitable for re-inserting into a Responses API ``input`` list."""
    # OpenAI SDK pydantic-v2 BaseModel
    for attr in ("model_dump", "to_dict", "as_dict"):
        fn = getattr(item, attr, None)
        if callable(fn):
            try:
                if attr == "model_dump":
                    return fn(exclude_none=True)
                return fn()
            except Exception:
                pass
    if isinstance(item, dict):
        return dict(item)
    # Last resort: attribute dump
    return {
        k: getattr(item, k)
        for k in dir(item)
        if not k.startswith("_") and not callable(getattr(item, k, None))
    }


# ---------------------------------------------------------------------------
# Public dispatcher
# ---------------------------------------------------------------------------



class GeoAgent:
    """Geospatial AI Agent dispatcher.

    Picks the strategy based on ``settings.agent_mode``:
    - ``chat_completion`` (default, dev): in-process agent + local/HTTP MCP tools.
    - ``foundry_agent_service`` (prod): hosted Foundry agent + remote MCP tools.

    The wire format yielded by :meth:`run_stream` is identical for both modes
    so the websocket router doesn't need to know which is in use.
    """

    def __init__(self) -> None:
        self._strategy: _ChatCompletionStrategy | _FoundryAgentServiceStrategy | None = None

    async def initialize(self) -> None:
        if settings.agent_mode == "foundry_agent_service":
            logger.info("Agent mode: foundry_agent_service")
            self._strategy = _FoundryAgentServiceStrategy()
        else:
            logger.info("Agent mode: chat_completion")
            self._strategy = _ChatCompletionStrategy()
        await self._strategy.initialize()

    async def cleanup(self) -> None:
        if self._strategy is not None:
            await self._strategy.cleanup()
        self._strategy = None

    async def run_stream(
        self, session_id: str, user_message: str
    ) -> AsyncIterator[dict]:
        if self._strategy is None:
            raise RuntimeError("Agent not initialized")
        async for event in self._strategy.run_stream(session_id, user_message):
            yield event


# Singleton agent instance
geo_agent = GeoAgent()
