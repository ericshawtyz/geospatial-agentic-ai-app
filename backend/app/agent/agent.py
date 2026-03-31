import json
import logging
import os
import sys
from collections.abc import AsyncIterator
from pathlib import Path

from agent_framework import (
    Agent,
    AgentSession,
    MCPStdioTool,
    Message,
)
from agent_framework_azure_ai import AzureAIClient
from azure.identity import DefaultAzureCredential

from app.agent.prompts import SYSTEM_PROMPT
from app.config import settings

logger = logging.getLogger("geo_agent")

_backend_dir = Path(__file__).resolve().parent.parent.parent
_python_exe = sys.executable


class GeoAgent:
    """Geospatial AI Agent with OneMap and URA MCP tool connections."""

    def __init__(self):
        self._agent: Agent | None = None
        self._onemap_mcp: MCPStdioTool | None = None
        self._ura_mcp: MCPStdioTool | None = None
        self._sessions: dict[str, AgentSession] = {}

    async def initialize(self):
        """Initialize Agent with AzureAIClient and MCP tools."""
        self._onemap_mcp = MCPStdioTool(
            name="onemap",
            command=_python_exe,
            args=["-m", "mcp_servers.onemap"],
            env={
                **os.environ,
                "ONEMAP_EMAIL": settings.onemap_email,
                "ONEMAP_PASSWORD": settings.onemap_password,
                "PYTHONPATH": str(_backend_dir),
            },
        )

        self._ura_mcp = MCPStdioTool(
            name="ura",
            command=_python_exe,
            args=["-m", "mcp_servers.ura"],
            env={
                **os.environ,
                "URA_ACCESS_KEY": settings.ura_access_key,
                "PYTHONPATH": str(_backend_dir),
            },
        )

        client = AzureAIClient(
            project_endpoint=settings.azure_ai_project_endpoint,
            model_deployment_name=settings.model_deployment_name,
            credential=DefaultAzureCredential(),
        )

        self._agent = Agent(
            client=client,
            instructions=SYSTEM_PROMPT,
            name="GeoAgent",
            description="Geospatial AI Agent for Singapore spatial data",
            tools=[self._onemap_mcp, self._ura_mcp],
        )

    async def cleanup(self):
        """Clean up resources."""
        self._agent = None
        self._onemap_mcp = None
        self._ura_mcp = None

    async def run_stream(self, session_id: str, user_message: str) -> AsyncIterator[dict]:
        """Stream agent response, yielding text deltas and tool call events."""
        if not self._agent:
            raise RuntimeError("Agent not initialized")

        if session_id not in self._sessions:
            self._sessions[session_id] = AgentSession(session_id=session_id)

        session = self._sessions[session_id]
        logger.info("[%s] User: %s", session_id[:8], user_message[:200])

        stream = self._agent.run(
            Message(role="user", text=user_message),
            session=session,
            stream=True,
        )

        # Track function calls by call_id to accumulate streamed arguments
        pending_calls: dict[str, dict] = {}  # call_id -> {name, args_parts}

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
                    name = (call_info["name"] if call_info else None) or content.name or "unknown"

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
                            result_str = json.dumps(raw_result, default=str, ensure_ascii=False)
                            if len(result_str) > 2000:
                                result_str = result_str[:2000] + "... (truncated)"
                        else:
                            result_str = str(getattr(content, "text", "") or "")
                    except Exception:
                        result_str = str(raw_result)[:2000] if raw_result else ""

                    logger.info("[%s] Tool result: %s len=%d", session_id[:8], name, len(result_str))
                    yield {
                        "type": "tool_call",
                        "name": name,
                        "arguments": args,
                        "status": "completed",
                        "result": result_str,
                    }

                elif content.type == "text":
                    delta = content.text or ""
                    if delta:
                        yield {"type": "delta", "text": delta}

        logger.info("[%s] Stream complete", session_id[:8])


# Singleton agent instance
geo_agent = GeoAgent()
