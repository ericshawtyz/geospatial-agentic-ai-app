import json as _json

from mcp_servers.onemap.server import mcp
from mcp_servers.onemap.auth import onemap_get


def _simplify_coords(coords: list, max_points: int = 60) -> list:
    """Downsample a coordinate ring to at most max_points entries."""
    if len(coords) <= max_points:
        return coords
    step = max(1, len(coords) // max_points)
    simplified = coords[::step]
    # Ensure the ring is closed
    if simplified[-1] != coords[-1]:
        simplified.append(coords[-1])
    return simplified


@mcp.tool()
async def get_all_planning_areas(year: str | None = None) -> dict:
    """Get a list of all planning area names in Singapore (metadata only, no polygon coordinates).

    Use get_planning_area_boundary to get the polygon for a specific planning area.

    Args:
        year: Planning area boundary year - '1998', '2008', '2014', or '2019'. Defaults to latest.
    """
    params = {}
    if year:
        params["year"] = year
    data = await onemap_get("/api/public/popapi/getAllPlanningarea", params)
    # Return only names — full polygons are too large for the model context
    areas = []
    for item in data if isinstance(data, list) else data.get("SearchResults", data.get("Result", [])):
        if isinstance(item, dict):
            name = item.get("pln_area_n") or item.get("name") or item.get("planning_area_name", "")
            if name:
                areas.append(name)
    return {"planning_areas": sorted(set(areas)), "count": len(set(areas)),
            "hint": "Use get_planning_area_boundary(name) to get the polygon for a specific area."}


@mcp.tool()
async def get_planning_area_boundary(planning_area_name: str, year: str | None = None) -> dict:
    """Get the polygon boundary of a single planning area for plotting on the map.

    Returns simplified polygon coordinates suitable for rendering.

    Args:
        planning_area_name: Name of the planning area (e.g. 'Tampines', 'Bedok', 'Jurong East'). Case-insensitive.
        year: Planning area boundary year - '1998', '2008', '2014', or '2019'. Defaults to latest.
    """
    params = {}
    if year:
        params["year"] = year
    data = await onemap_get("/api/public/popapi/getAllPlanningarea", params)

    target = planning_area_name.strip().upper()
    items = data if isinstance(data, list) else data.get("SearchResults", data.get("Result", []))

    for item in items:
        if not isinstance(item, dict):
            continue
        name = (item.get("pln_area_n") or item.get("name") or "").strip().upper()
        if name != target:
            continue

        # Extract and simplify polygon coordinates
        geojson = item.get("geojson")
        if isinstance(geojson, str):
            try:
                geojson = _json.loads(geojson)
            except Exception:
                pass

        if isinstance(geojson, dict):
            geom_type = geojson.get("type", "")
            coords = geojson.get("coordinates", [])

            if geom_type == "Polygon" and coords:
                coords = [_simplify_coords(ring) for ring in coords]
            elif geom_type == "MultiPolygon" and coords:
                coords = [[_simplify_coords(ring) for ring in poly] for poly in coords]

            return {
                "name": item.get("pln_area_n") or planning_area_name,
                "geojson": {"type": geom_type, "coordinates": coords},
            }

        # Fallback: return raw coordinate fields if present
        return {
            "name": item.get("pln_area_n") or planning_area_name,
            "raw_item_keys": list(item.keys()),
        }

    return {"error": f"Planning area '{planning_area_name}' not found.",
            "hint": "Use get_all_planning_areas() to list valid names."}


@mcp.tool()
async def get_planning_area_names(year: str | None = None) -> dict:
    """Get a list of all planning area names in Singapore.

    Args:
        year: Planning area boundary year - '1998', '2008', '2014', or '2019'. Defaults to latest.
    """
    params = {}
    if year:
        params["year"] = year
    return await onemap_get("/api/public/popapi/getPlanningareaNames", params)


@mcp.tool()
async def get_planning_area(
    latitude: str, longitude: str, year: str | None = None
) -> dict:
    """Find which planning area a location falls in.

    Args:
        latitude: WGS84 latitude
        longitude: WGS84 longitude
        year: Planning area boundary year - '1998', '2008', '2014', or '2019'. Defaults to latest.
    """
    params: dict = {"latitude": latitude, "longitude": longitude}
    if year:
        params["year"] = year
    return await onemap_get("/api/public/popapi/getPlanningarea", params)
