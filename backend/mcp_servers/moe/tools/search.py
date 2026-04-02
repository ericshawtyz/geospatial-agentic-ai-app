from mcp_servers.moe.http import moe_get
from mcp_servers.moe.server import mcp


@mcp.tool()
async def search(
    searchVal: str,
    returnGeom: str = "Y",
    getAddrDetails: str = "Y",
) -> dict:
    """Search for an address by Singapore postal code. Returns address details including latitude, longitude, and block number.

    Args:
        searchVal: Singapore postal code to search for.
        returnGeom: 'Y' to return geometry coordinates, 'N' to skip. Defaults to 'Y'.
        getAddrDetails: 'Y' to return full address details, 'N' to skip. Defaults to 'Y'.
    """
    params = {
        "searchVal": searchVal,
        "returnGeom": returnGeom,
        "getAddrDetails": getAddrDetails,
    }
    return await moe_get("/api/onemap/common/elastic/search", params)
