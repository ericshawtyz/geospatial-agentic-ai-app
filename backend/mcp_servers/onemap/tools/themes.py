from mcp_servers.onemap.auth import onemap_get
from mcp_servers.onemap.server import mcp


@mcp.tool()
async def get_all_themes(moreInfo: str = "N") -> dict:
    """Get a list of all available OneMap themes (data layers).

    Args:
        moreInfo: 'Y' to include icon URL, category, and owner info. 'N' for basic info.
    """
    return await onemap_get(
        "/api/public/themesvc/getAllThemesInfo", {"moreInfo": moreInfo}
    )


@mcp.tool()
async def get_theme_info(queryName: str) -> dict:
    """Get information about a specific OneMap theme.

    Args:
        queryName: The theme query name (from get_all_themes results)
    """
    return await onemap_get(
        "/api/public/themesvc/getThemeInfo", {"queryName": queryName}
    )


@mcp.tool()
async def check_theme_status(queryName: str, dateTime: str) -> dict:
    """Check if a theme has been updated since a given datetime.

    Args:
        queryName: The theme query name
        dateTime: Datetime in ISO format 'YYYY-MM-DDTHH:MM:SS.FFFZ'
    """
    return await onemap_get(
        "/api/public/themesvc/checkThemeStatus",
        {"queryName": queryName, "dateTime": dateTime},
    )


@mcp.tool()
async def retrieve_theme(queryName: str, extents: str | None = None) -> dict:
    """Retrieve theme data (features/points) for a specific OneMap theme.

    Args:
        queryName: The theme query name
        extents: Optional boundary filter as 'lat1,lng1,lat2,lng2' (WGS84). Strongly recommended to avoid very large responses.
    """
    params: dict = {"queryName": queryName}
    if extents:
        params["extents"] = extents
    result = await onemap_get("/api/public/themesvc/retrieveTheme", params)

    # Cap the number of features to prevent context-window overflow.
    # The first item in SrchResults is metadata; the rest are features.
    _MAX_FEATURES = 50
    if isinstance(result, dict) and "SrchResults" in result:
        items = result["SrchResults"]
        if isinstance(items, list) and len(items) > _MAX_FEATURES + 1:
            total = len(items) - 1  # exclude metadata row
            result["SrchResults"] = items[: _MAX_FEATURES + 1]
            result["_truncated"] = True
            result["_total_features"] = total
            result["_returned_features"] = _MAX_FEATURES

    return result
