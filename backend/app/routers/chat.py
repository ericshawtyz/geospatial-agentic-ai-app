import json
import logging
import time
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agent.agent import geo_agent

logger = logging.getLogger("chat_ws")

router = APIRouter()


@router.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())
    logger.info("[%s] WebSocket connected", session_id[:8])

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            user_message = data.get("message", "")
            file_context = data.get("fileContext")
            user_location = data.get("userLocation")  # {lat, lng} from browser

            # Build the full user input, including any file context
            full_input = user_message
            if user_location:
                full_input += (
                    f"\n\n[User's current browser location: "
                    f"latitude={user_location['lat']}, longitude={user_location['lng']}. "
                    f"Use this for any 'nearby' or 'closest' queries unless the user specifies a different location.]"
                )
            if file_context:
                full_input += f"\n\n[Uploaded file context]\n{json.dumps(file_context, indent=2)}"

            logger.info("[%s] >>> User: %s", session_id[:8], user_message[:200])
            t0 = time.perf_counter()
            tool_count = 0
            delta_count = 0

            # Stream chunks to client
            full_response = ""
            async for event in geo_agent.run_stream(session_id, full_input):
                if event["type"] == "delta":
                    full_response += event["text"]
                    delta_count += 1
                    await websocket.send_text(
                        json.dumps({"type": "delta", "text": event["text"]})
                    )
                elif event["type"] == "tool_call":
                    tool_count += 1
                    logger.info(
                        "[%s]   tool %s status=%s",
                        session_id[:8],
                        event["name"],
                        event["status"],
                    )
                    await websocket.send_text(
                        json.dumps({
                            "type": "tool_call",
                            "name": event["name"],
                            "arguments": event["arguments"],
                            "status": event["status"],
                            "result": event["result"],
                        })
                    )

            elapsed = time.perf_counter() - t0

            # Parse the complete response for map commands
            text_content, map_commands = _parse_agent_response(full_response)

            logger.info(
                "[%s] <<< Done in %.1fs | %d deltas | %d tool calls | %d map cmds | response len=%d",
                session_id[:8],
                elapsed,
                delta_count,
                tool_count,
                len(map_commands),
                len(full_response),
            )

            # Send final message with cleaned text and map commands
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "done",
                        "text": text_content,
                        "mapCommands": map_commands,
                    }
                )
            )

    except WebSocketDisconnect:
        logger.info("[%s] WebSocket disconnected", session_id[:8])
    except Exception as e:
        logger.exception("[%s] Error: %s", session_id[:8], e)
        try:
            await websocket.send_text(
                json.dumps({"type": "error", "text": str(e)})
            )
        except Exception:
            pass


def _parse_agent_response(response: str) -> tuple[str, list[dict]]:
    """Extract text content and mapCommands JSON blocks from agent response."""
    import re

    blocks = _find_map_command_blocks(response)
    if not blocks:
        return response, []

    map_commands: list[dict] = []
    for _, _, cmds in blocks:
        map_commands.extend(cmds)

    # Remove found blocks from text (reverse order preserves indices)
    text_content = response
    for start, end, _ in reversed(blocks):
        text_content = text_content[:start] + text_content[end:]

    # Clean up leftover whitespace / blank lines
    text_content = re.sub(r"\n{3,}", "\n\n", text_content)
    text_content = text_content.strip()
    return text_content, map_commands


def _find_map_command_blocks(text: str) -> list[tuple[int, int, list[dict]]]:
    """Locate JSON objects containing 'mapCommands' using bracket-counting
    to correctly handle nested braces/arrays and quoted strings."""
    results: list[tuple[int, int, list[dict]]] = []
    search_from = 0

    while search_from < len(text):
        key_idx = text.find('"mapCommands"', search_from)
        if key_idx == -1:
            break

        # Walk backwards over whitespace to find the opening brace
        obj_start = key_idx - 1
        while obj_start >= 0 and text[obj_start] in " \t\n\r":
            obj_start -= 1
        if obj_start < 0 or text[obj_start] != "{":
            search_from = key_idx + 1
            continue

        # Forward-scan from the opening brace with bracket counting
        depth = 0
        i = obj_start
        obj_end = -1
        while i < len(text):
            ch = text[i]
            if ch == '"':
                # Skip entire JSON string (handle escape sequences)
                i += 1
                while i < len(text):
                    if text[i] == "\\":
                        i += 2
                        continue
                    if text[i] == '"':
                        break
                    i += 1
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    obj_end = i + 1
                    break
            i += 1

        if obj_end == -1:
            search_from = key_idx + 1
            continue

        # Try to parse the candidate JSON
        candidate = text[obj_start:obj_end]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed.get("mapCommands"), list):
                results.append((obj_start, obj_end, parsed["mapCommands"]))
        except json.JSONDecodeError:
            pass

        search_from = obj_end

    return results
