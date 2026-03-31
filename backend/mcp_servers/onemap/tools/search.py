from mcp_servers.onemap.server import mcp
from mcp_servers.onemap.auth import onemap_get


@mcp.tool()
async def search(
    searchVal: str,
    returnGeom: str = "Y",
    getAddrDetails: str = "Y",
    pageNum: int | None = None,
) -> dict:
    """Search for addresses, buildings, postal codes, or bus stops in Singapore.

    Args:
        searchVal: Keywords to search (building name, road name, postal code, bus stop code, etc.)
        returnGeom: 'Y' to return geometry coordinates, 'N' to skip
        getAddrDetails: 'Y' to return full address details, 'N' to skip
        pageNum: Page number for paginated results (optional)
    """
    params: dict = {
        "searchVal": searchVal,
        "returnGeom": returnGeom,
        "getAddrDetails": getAddrDetails,
    }
    if pageNum is not None:
        params["pageNum"] = pageNum
    return await onemap_get("/api/common/elastic/search", params)
