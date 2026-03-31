from mcp_servers.onemap.server import mcp
from mcp_servers.onemap.auth import onemap_get


@mcp.tool()
async def convert_4326_to_3857(latitude: str, longitude: str) -> dict:
    """Convert WGS84 (EPSG:4326) coordinates to Web Mercator (EPSG:3857).

    Args:
        latitude: WGS84 latitude
        longitude: WGS84 longitude
    """
    return await onemap_get(
        "/api/common/convert/4326to3857",
        {"latitude": latitude, "longitude": longitude},
    )


@mcp.tool()
async def convert_4326_to_3414(latitude: str, longitude: str) -> dict:
    """Convert WGS84 (EPSG:4326) coordinates to SVY21 (EPSG:3414).

    Args:
        latitude: WGS84 latitude
        longitude: WGS84 longitude
    """
    return await onemap_get(
        "/api/common/convert/4326to3414",
        {"latitude": latitude, "longitude": longitude},
    )


@mcp.tool()
async def convert_3414_to_3857(X: str, Y: str) -> dict:
    """Convert SVY21 (EPSG:3414) coordinates to Web Mercator (EPSG:3857).

    Args:
        X: SVY21 X coordinate (easting)
        Y: SVY21 Y coordinate (northing)
    """
    return await onemap_get(
        "/api/common/convert/3414to3857", {"X": X, "Y": Y}
    )


@mcp.tool()
async def convert_3414_to_4326(X: str, Y: str) -> dict:
    """Convert SVY21 (EPSG:3414) coordinates to WGS84 (EPSG:4326).

    Args:
        X: SVY21 X coordinate (easting)
        Y: SVY21 Y coordinate (northing)
    """
    return await onemap_get(
        "/api/common/convert/3414to4326", {"X": X, "Y": Y}
    )


@mcp.tool()
async def convert_3857_to_3414(X: str, Y: str) -> dict:
    """Convert Web Mercator (EPSG:3857) coordinates to SVY21 (EPSG:3414).

    Args:
        X: Web Mercator X coordinate
        Y: Web Mercator Y coordinate
    """
    return await onemap_get(
        "/api/common/convert/3857to3414", {"X": X, "Y": Y}
    )


@mcp.tool()
async def convert_3857_to_4326(X: str, Y: str) -> dict:
    """Convert Web Mercator (EPSG:3857) coordinates to WGS84 (EPSG:4326).

    Args:
        X: Web Mercator X coordinate
        Y: Web Mercator Y coordinate
    """
    return await onemap_get(
        "/api/common/convert/3857to4326", {"X": X, "Y": Y}
    )
