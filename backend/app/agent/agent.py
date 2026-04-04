import json
import logging
import re
import sys
import time
from collections.abc import AsyncIterator
from pathlib import Path

# Pattern to strip Bing grounding citation tags like citeturn0search0
_CITE_TAG_RE = re.compile(r"\bciteturn\d+search\d+\b")
_CITE_HOLDBACK = 25  # max chars to buffer for split citation tags

from typing import Annotated

from agent_framework import (
    Agent,
    AgentSession,
    MCPStdioTool,
    MCPStreamableHTTPTool,
    Message,
)
from agent_framework_azure_ai import AzureAIClient
from azure.identity import DefaultAzureCredential

from app.agent.prompts import SYSTEM_PROMPT
from app.config import settings
from app.services.school_data import search_school

logger = logging.getLogger("geo_agent")

_backend_dir = Path(__file__).resolve().parent.parent.parent
_python_exe = sys.executable
_base_env = {"PYTHONPATH": str(_backend_dir), "PATH": sys.prefix}

_SESSION_MAX_AGE = 30 * 60  # 30 minutes
_SESSION_CLEANUP_INTERVAL = 5 * 60  # check every 5 minutes


class GeoAgent:
    """Geospatial AI Agent with OneMap, URA, and MOE MCP tool connections."""

    def __init__(self):
        self._agent: Agent | None = None
        self._onemap_mcp: MCPStdioTool | MCPStreamableHTTPTool | None = None
        self._ura_mcp: MCPStdioTool | MCPStreamableHTTPTool | None = None
        self._moe_mcp: MCPStdioTool | MCPStreamableHTTPTool | None = None
        self._sessions: dict[str, tuple[AgentSession, float]] = (
            {}
        )  # id -> (session, last_used)
        self._last_cleanup = 0.0

    async def initialize(self):
        """Initialize Agent with MCP tools."""
        # --- OneMap MCP tool ---
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

        # --- URA MCP tool ---
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

        # --- MOE MCP tool ---
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

        tools = [self._onemap_mcp, self._ura_mcp, self._moe_mcp]

        # --- School detail lookup (local JSON + fuzzy match) ---
        def lookup_school_details(
            school_name: Annotated[str, "The name of the school to look up (e.g. 'St Hilda\'s Primary School')"]
        ) -> str:
            """Look up detailed information about a Singapore school by name.

            Returns general info, subjects offered, CCAs, distinctive programmes,
            and more. Uses fuzzy matching to handle typos and abbreviations.
            """
            result = search_school(school_name)
            if result is None:
                return json.dumps({"error": f"No school found matching '{school_name}'. Try a more specific name."})
            return json.dumps(result, default=str)

        tools.append(lookup_school_details)
        logger.info("School detail lookup tool enabled (%s)", "local JSON")

        credential = DefaultAzureCredential()

        client = AzureAIClient(
            project_endpoint=settings.azure_ai_project_endpoint,
            model_deployment_name=settings.model_deployment_name,
            credential=credential,
        )
        tools.append(AzureAIClient.get_web_search_tool())
        logger.info("Bing web search tool enabled")

        self._agent = Agent(
            client=client,
            instructions=SYSTEM_PROMPT,
            name="GeoAgent",
            description="Geospatial AI Agent for Singapore spatial data",
            tools=tools,
        )

    async def cleanup(self):
        """Clean up resources and close MCP subprocesses."""
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
        self._agent = None
        self._onemap_mcp = None
        self._ura_mcp = None
        self._moe_mcp = None
        self._sessions.clear()

    def _evict_stale_sessions(self) -> None:
        """Remove sessions idle for longer than _SESSION_MAX_AGE."""
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
        """Stream agent response, yielding text deltas and tool call events."""
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
            Message(role="user", text=user_message),
            session=session,
            stream=True,
        )

        # Track function calls by call_id to accumulate streamed arguments
        pending_calls: dict[str, dict] = {}  # call_id -> {name, args_parts}
        # Track server-side web search (Bing grounding) — no function_call events
        web_search_emitted = False
        web_search_citations: list[dict] = []
        # Buffer for stripping citation tags that may be split across chunks
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
                        # First chunk for this call — emit "executing" event
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

                    # Parse accumulated arguments
                    args = {}
                    if call_info and call_info["args_parts"]:
                        raw = "".join(call_info["args_parts"])
                        try:
                            args = json.loads(raw)
                        except Exception:
                            args = {"raw": raw}

                    # Parse result
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

                    # Keep full result for fallback map extraction; truncate for display
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
                    # Detect server-side Bing web search via citation annotations
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
                        # Accumulate text in buffer to catch citation tags
                        # split across streaming chunks
                        cite_buffer += delta
                        cite_buffer = _CITE_TAG_RE.sub("", cite_buffer)
                        # Hold back last N chars in case a tag is partially streamed
                        if len(cite_buffer) > _CITE_HOLDBACK:
                            safe = cite_buffer[:-_CITE_HOLDBACK]
                            cite_buffer = cite_buffer[-_CITE_HOLDBACK:]
                            if safe:
                                yield {"type": "delta", "text": safe}

        # Flush remaining buffered text
        if cite_buffer:
            cite_buffer = _CITE_TAG_RE.sub("", cite_buffer)
            if cite_buffer:
                yield {"type": "delta", "text": cite_buffer}

        # Emit completed event for server-side web search
        if web_search_emitted:
            sources = (
                "\n".join(f"- [{c['title']}]({c['url']})" for c in web_search_citations)
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


# Singleton agent instance
geo_agent = GeoAgent()
