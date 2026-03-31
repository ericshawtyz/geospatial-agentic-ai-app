from mcp_servers.onemap.server import mcp
from mcp_servers.onemap.auth import onemap_get


@mcp.tool()
async def get_route(
    start: str,
    end: str,
    routeType: str,
    date: str | None = None,
    time: str | None = None,
    mode: str | None = None,
    maxWalkDistance: int | None = None,
    numItineraries: int | None = None,
) -> dict:
    """Get routing directions between two points in Singapore.

    Args:
        start: Start point as 'latitude,longitude' (WGS84)
        end: End point as 'latitude,longitude' (WGS84)
        routeType: Route type - 'walk', 'drive', 'cycle', or 'pt' (public transport)
        date: Required for 'pt' route type. Date in 'MM-DD-YYYY' format.
        time: Required for 'pt' route type. Time in 'HH:MM:SS' (24h format).
        mode: For 'pt' only - 'TRANSIT', 'BUS', or 'RAIL'
        maxWalkDistance: For 'pt' only - max walk distance in meters
        numItineraries: For 'pt' only - number of itineraries (1-3)
    """
    params: dict = {
        "start": start,
        "end": end,
        "routeType": routeType,
    }
    if date:
        params["date"] = date
    if time:
        params["time"] = time
    if mode:
        params["mode"] = mode
    if maxWalkDistance is not None:
        params["maxWalkDistance"] = maxWalkDistance
    if numItineraries is not None:
        params["numItineraries"] = numItineraries
    return await onemap_get("/api/public/routingsvc/route", params)
