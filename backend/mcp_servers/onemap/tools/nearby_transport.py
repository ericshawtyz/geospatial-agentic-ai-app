from mcp_servers.onemap.server import mcp
from mcp_servers.onemap.auth import onemap_get


@mcp.tool()
async def get_nearest_mrt_stops(
    latitude: float, longitude: float, radius_in_meters: int = 2000
) -> dict:
    """Find nearest MRT/LRT stations to a location.

    Args:
        latitude: WGS84 latitude
        longitude: WGS84 longitude
        radius_in_meters: Search radius in meters (default 2000, max 5000)
    """
    return await onemap_get(
        "/api/public/nearbysvc/getNearestMrtStops",
        {
            "latitude": latitude,
            "longitude": longitude,
            "radius_in_meters": radius_in_meters,
        },
    )


@mcp.tool()
async def get_nearest_bus_stops(
    latitude: float, longitude: float, radius_in_meters: int = 2000
) -> dict:
    """Find nearest bus stops to a location.

    Args:
        latitude: WGS84 latitude
        longitude: WGS84 longitude
        radius_in_meters: Search radius in meters (default 2000, max 5000)
    """
    return await onemap_get(
        "/api/public/nearbysvc/getNearestBusStops",
        {
            "latitude": latitude,
            "longitude": longitude,
            "radius_in_meters": radius_in_meters,
        },
    )
