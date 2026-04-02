from mcp_servers.moe.http import moe_get
from mcp_servers.moe.server import mcp


@mcp.tool()
async def nearby_secondary_schools(
    latitude: float,
    longitude: float,
    distance: int = 5000,
) -> dict:
    """Query secondary schools near a given location in Singapore.

    Args:
        latitude: Latitude of the location (can be retrieved from the search tool).
        longitude: Longitude of the location (can be retrieved from the search tool).
        distance: Search radius in metres. Defaults to 5000.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "distance": distance,
    }
    return await moe_get("/api/onemap/moe/nearbySecondarySchools", params)
