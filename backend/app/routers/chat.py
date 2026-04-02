import json
import logging
import re
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
                full_input += (
                    f"\n\n[Uploaded file context]\n{json.dumps(file_context, indent=2)}"
                )

            logger.info("[%s] >>> User: %s", session_id[:8], user_message[:200])
            t0 = time.perf_counter()
            tool_count = 0
            delta_count = 0
            tool_results: list[dict] = []  # Track completed tool results for fallback

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
                    if event["status"] == "completed" and event.get("result"):
                        tool_results.append(
                            {
                                "name": event["name"],
                                "result": event.get("full_result") or event["result"],
                            }
                        )
                    logger.info(
                        "[%s]   tool %s status=%s",
                        session_id[:8],
                        event["name"],
                        event["status"],
                    )
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "tool_call",
                                "name": event["name"],
                                "arguments": event["arguments"],
                                "status": event["status"],
                                "result": event["result"],
                            }
                        )
                    )

            elapsed = time.perf_counter() - t0

            # Parse the complete response for map commands
            text_content, map_commands = _parse_agent_response(full_response)

            # Fallback: if the agent used tools but forgot mapCommands,
            # try to auto-extract from tool results (GeoJSON) or response text.
            if not map_commands and tool_count > 0:
                fallback_cmds = _extract_fallback_from_tool_results(tool_results)
                if not fallback_cmds:
                    fallback_cmds = _extract_fallback_map_commands(full_response)
                if fallback_cmds:
                    map_commands = fallback_cmds
                    logger.info(
                        "[%s]   ↳ injected %d fallback map commands",
                        session_id[:8],
                        len(fallback_cmds),
                    )

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
            await websocket.send_text(json.dumps({"type": "error", "text": str(e)}))
        except Exception:
            pass


def _parse_agent_response(response: str) -> tuple[str, list[dict]]:
    """Extract text content and mapCommands JSON blocks from agent response."""
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


def _extract_fallback_from_tool_results(tool_results: list[dict]) -> list[dict]:
    """Build map commands from tool results that contain GeoJSON or coordinate data."""
    commands: list[dict] = []
    markers: list[dict] = []

    for tr in tool_results:
        result_str = tr.get("result", "")
        try:
            result_data = (
                json.loads(result_str) if isinstance(result_str, str) else result_str
            )
        except (json.JSONDecodeError, TypeError):
            continue

        if not isinstance(result_data, dict):
            continue

        # Case 1: Tool returned a geojson field (e.g. get_planning_area_boundary)
        geojson = result_data.get("geojson")
        if isinstance(geojson, dict) and geojson.get("type") in (
            "Polygon",
            "MultiPolygon",
            "Point",
            "MultiPoint",
            "LineString",
            "MultiLineString",
            "GeometryCollection",
            "Feature",
            "FeatureCollection",
        ):
            name = result_data.get("name", "")
            # Wrap bare geometry in a FeatureCollection
            if geojson["type"] in ("Feature", "FeatureCollection"):
                fc = geojson
            else:
                fc = {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "properties": {"label": name},
                            "geometry": geojson,
                        }
                    ],
                }

            # Compute centroid from coordinates for setView
            centroid = _geojson_centroid(geojson)

            if not commands:
                commands.append({"action": "clearMap", "data": {}})

            if centroid:
                commands.append(
                    {
                        "action": "setView",
                        "data": {"lat": centroid[0], "lng": centroid[1], "zoom": 13},
                    }
                )

            commands.append(
                {
                    "action": "addGeoJSON",
                    "data": {
                        "geojson": fc,
                        "style": {"color": "#3388ff", "weight": 3, "fillOpacity": 0.6},
                    },
                }
            )

        # Case 2: Tool returned results with lat/lng fields (e.g. search results)
        for key in ("results", "SearchResults", "Result"):
            items = result_data.get(key)
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                lat = item.get("LATITUDE") or item.get("latitude") or item.get("lat")
                lng = item.get("LONGITUDE") or item.get("longitude") or item.get("lng")
                if lat is not None and lng is not None:
                    try:
                        lat_f, lng_f = float(lat), float(lng)
                        if 1.1 <= lat_f <= 1.5 and 103.5 <= lng_f <= 104.1:
                            label = (
                                item.get("SEARCHVAL")
                                or item.get("BUILDING")
                                or item.get("ADDRESS")
                                or item.get("name")
                                or ""
                            )
                            markers.append(
                                {
                                    "lat": lat_f,
                                    "lng": lng_f,
                                    "label": label,
                                    "popup": label,
                                }
                            )
                    except (ValueError, TypeError):
                        pass

    if markers and not commands:
        commands.append({"action": "clearMap", "data": {}})
        avg_lat = sum(m["lat"] for m in markers) / len(markers)
        avg_lng = sum(m["lng"] for m in markers) / len(markers)
        commands.append(
            {
                "action": "setView",
                "data": {
                    "lat": avg_lat,
                    "lng": avg_lng,
                    "zoom": 15 if len(markers) <= 3 else 13,
                },
            }
        )
        commands.append({"action": "addMarkers", "data": {"markers": markers}})

    return commands


def _geojson_centroid(geojson: dict) -> list[float] | None:
    """Compute approximate centroid [lat, lng] from GeoJSON geometry."""
    coords = []

    def _collect(obj: dict) -> None:
        gtype = obj.get("type", "")
        raw = obj.get("coordinates", [])
        if gtype == "Point" and raw:
            coords.append(raw)
        elif gtype in ("LineString", "MultiPoint") and raw:
            coords.extend(raw)
        elif gtype in ("Polygon", "MultiLineString") and raw:
            for ring in raw:
                if isinstance(ring, list):
                    coords.extend(
                        r for r in ring if isinstance(r, list) and len(r) >= 2
                    )
        elif gtype == "MultiPolygon" and raw:
            for poly in raw:
                for ring in poly:
                    if isinstance(ring, list):
                        coords.extend(
                            r for r in ring if isinstance(r, list) and len(r) >= 2
                        )
        elif gtype == "Feature":
            geom = obj.get("geometry")
            if isinstance(geom, dict):
                _collect(geom)
        elif gtype == "FeatureCollection":
            for feat in obj.get("features", []):
                if isinstance(feat, dict):
                    _collect(feat)

    _collect(geojson)
    if not coords:
        return None

    # GeoJSON is [lng, lat]; return [lat, lng]
    lats = [c[1] for c in coords]
    lngs = [c[0] for c in coords]
    return [(min(lats) + max(lats)) / 2, (min(lngs) + max(lngs)) / 2]


def _extract_fallback_map_commands(text: str) -> list[dict]:
    """Best-effort extraction of coordinate pairs from agent text when mapCommands are missing.

    Scans for patterns like 'latitude=1.3, longitude=103.8' or '(1.3, 103.8)' or
    explicit 'lat.*1.3.*lng.*103.8' and builds addMarkers + setView commands.
    """
    markers: list[dict] = []
    seen: set[tuple[float, float]] = set()

    # Capture lat/lng pairs in various formats
    pair_pattern = re.compile(
        r"lat(?:itude)?\s*[:=]\s*(-?\d+\.\d+)\s*[,;/\s]+\s*(?:lon(?:gitude)?|lng)\s*[:=]\s*(-?\d+\.\d+)",
        re.IGNORECASE,
    )
    for m in pair_pattern.finditer(text):
        lat, lng = float(m.group(1)), float(m.group(2))
        if 1.1 <= lat <= 1.5 and 103.5 <= lng <= 104.1 and (lat, lng) not in seen:
            seen.add((lat, lng))
            markers.append({"lat": lat, "lng": lng, "label": "", "popup": ""})

    # Pattern 2: coordinates like (1.3521, 103.8198) within Singapore bounds
    coord_pattern = re.compile(r"\(\s*(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)\s*\)")
    for m in coord_pattern.finditer(text):
        a, b = float(m.group(1)), float(m.group(2))
        # Determine which is lat vs lng by Singapore bounds
        if 1.1 <= a <= 1.5 and 103.5 <= b <= 104.1 and (a, b) not in seen:
            seen.add((a, b))
            markers.append({"lat": a, "lng": b, "label": "", "popup": ""})

    if not markers:
        return []

    # Build map commands
    commands: list[dict] = [{"action": "clearMap", "data": {}}]

    # Center on the first marker or centroid
    avg_lat = sum(m["lat"] for m in markers) / len(markers)
    avg_lng = sum(m["lng"] for m in markers) / len(markers)
    zoom = 15 if len(markers) <= 3 else 13
    commands.append(
        {"action": "setView", "data": {"lat": avg_lat, "lng": avg_lng, "zoom": zoom}}
    )
    commands.append({"action": "addMarkers", "data": {"markers": markers}})

    return commands
