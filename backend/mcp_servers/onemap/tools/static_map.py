from mcp_servers.onemap.server import mcp
from mcp_servers.onemap.auth import onemap_get


@mcp.tool()
async def get_static_map(
    layerchosen: str,
    zoom: int,
    width: int,
    height: int,
    latitude: str | None = None,
    longitude: str | None = None,
    postal: str | None = None,
    points: str | None = None,
    lines: str | None = None,
    polygons: str | None = None,
    color: str | None = None,
    fillColor: str | None = None,
) -> dict:
    """Generate a static map image URL from OneMap.

    Args:
        layerchosen: Basemap style - 'default', 'night', 'grey', 'original', or 'landlot'
        zoom: Zoom level (11-19)
        width: Image width in pixels (128-512)
        height: Image height in pixels (128-512)
        latitude: WGS84 latitude (required if postal not provided)
        longitude: WGS84 longitude (required if postal not provided)
        postal: Singapore postal code (alternative to lat/lng)
        points: Point markers as '[lat,lng,"R,G,B"]|[lat,lng,"R,G,B"]'
        lines: Line coordinates + color + thickness, semicolon-separated. Pipes separate lines.
        polygons: Polygon coordinates + color, semicolon-separated. Pipes separate polygons.
        color: Line color as 'R,G,B' (e.g. '255,0,255')
        fillColor: Polygon fill color as 'R,G,B' (e.g. '0,255,0')
    """
    params: dict = {
        "layerchosen": layerchosen,
        "zoom": zoom,
        "width": width,
        "height": height,
    }
    if latitude:
        params["latitude"] = latitude
    if longitude:
        params["longitude"] = longitude
    if postal:
        params["postal"] = postal
    if points:
        params["points"] = points
    if lines:
        params["lines"] = lines
    if polygons:
        params["polygons"] = polygons
    if color:
        params["color"] = color
    if fillColor:
        params["fillColor"] = fillColor

    # Build the URL for the static map (returns an image, not JSON)
    from mcp_servers.onemap.auth import BASE_URL, get_token

    token = await get_token()
    query_parts = [f"{k}={v}" for k, v in params.items()]
    url = f"{BASE_URL}/api/staticmap/getStaticImage?{'&'.join(query_parts)}"
    return {"staticMapUrl": url, "authToken": token}
