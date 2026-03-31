from mcp_servers.onemap.server import mcp
from mcp_servers.onemap.auth import onemap_get


@mcp.tool()
async def retrieve_lot_info_by_lot_key(lotkey: str) -> dict:
    """Retrieve land lot information based on a lot key.

    Args:
        lotkey: The lot key identifier (e.g. 'TS23U000324L')
    """
    return await onemap_get(
        "/api/ura/retrieveLotInfoBasedOnLotKey", {"lotkey": lotkey}
    )


@mcp.tool()
async def retrieve_land_lot(latitude: float, longitude: float) -> dict:
    """Retrieve land lot information for a given coordinate.

    Args:
        latitude: WGS84 latitude (e.g. 1.300055494)
        longitude: WGS84 longitude (e.g. 103.7988114)
    """
    return await onemap_get(
        "/api/ura/retrieveLandLot",
        {"latitude": latitude, "longitude": longitude},
    )


@mcp.tool()
async def retrieve_land_ownership(lotNo: str) -> dict:
    """Retrieve land ownership information for a land lot number.

    Args:
        lotNo: The MK/TS lot number (e.g. 'MK26-08092A')
    """
    return await onemap_get(
        "/api/ura/retrieveLandOwnershipForLandLot", {"lotNo": lotNo}
    )


@mcp.tool()
async def retrieve_land_lot_search(searchVal: str, pageNum: int | None = None) -> dict:
    """Search for land lots by MK/TS number prefix.

    Args:
        searchVal: Search value - MK/TS lot number prefix (e.g. 'MK26')
        pageNum: Page number for paginated results (optional)
    """
    params: dict = {"searchVal": searchVal}
    if pageNum is not None:
        params["pageNum"] = pageNum
    return await onemap_get("/api/ura/retrieveLandLotSearch", params)


@mcp.tool()
async def retrieve_lot_info_with_attributes(
    postal: str, hsenumber: str, floorno: str, unitno: str
) -> dict:
    """Retrieve lot information with attributes for a specific address unit.

    Args:
        postal: Singapore postal code (e.g. '238869')
        hsenumber: House/block number (e.g. '360')
        floorno: Floor number (e.g. '4')
        unitno: Unit number (e.g. '0')
    """
    return await onemap_get(
        "/api/ura/retrieveLotInfoWithAttributes",
        {
            "postal": postal,
            "hsenumber": hsenumber,
            "floorno": floorno,
            "unitno": unitno,
        },
    )
