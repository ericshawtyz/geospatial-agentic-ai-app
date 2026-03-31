from mcp_servers.onemap.server import mcp
from mcp_servers.onemap.auth import onemap_get


@mcp.tool()
async def reverse_geocode_wgs84(
    location: str,
    buffer: int | None = None,
    addressType: str | None = None,
) -> dict:
    """Reverse geocode WGS84 coordinates to find nearby buildings/addresses.

    Args:
        location: Latitude,Longitude in WGS84 format (e.g. '1.3,103.8')
        buffer: Search radius in meters (0-500). Default returns nearest.
        addressType: 'HDB' for HDB addresses only, 'All' for all types
    """
    params: dict = {"location": location}
    if buffer is not None:
        params["buffer"] = buffer
    if addressType:
        params["addressType"] = addressType
    return await onemap_get("/api/public/revgeocode", params)


@mcp.tool()
async def reverse_geocode_svy21(
    location: str,
    buffer: int | None = None,
    addressType: str | None = None,
) -> dict:
    """Reverse geocode SVY21 coordinates to find nearby buildings/addresses.

    Args:
        location: X,Y coordinates in SVY21 format (e.g. '28983.788,33554.568')
        buffer: Search radius in meters (0-500). Default returns nearest.
        addressType: 'HDB' for HDB addresses only, 'All' for all types
    """
    params: dict = {"location": location}
    if buffer is not None:
        params["buffer"] = buffer
    if addressType:
        params["addressType"] = addressType
    return await onemap_get("/api/public/revgeocodexy", params)
