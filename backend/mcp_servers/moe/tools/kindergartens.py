from mcp_servers.moe.http import moe_get
from mcp_servers.moe.server import mcp


@mcp.tool()
async def query_kindergartens(
    postalcode: str,
    blk_no: str,
) -> dict:
    """Query MOE kindergartens near a given address in Singapore.

    IMPORTANT: The blk_no parameter is NOT the postal code. You must first call
    the moe search tool with the postal code. The search result contains a BLK_NO
    field (e.g. "625B") — pass that value as blk_no here.

    The response includes a dist_code field for each kindergarten:
      - dist_code "1" = within 1 km of the address
      - dist_code "2" = between 1-2 km of the address

    Args:
        postalcode: Singapore postal code of the address.
        blk_no: The BLK_NO value from the moe search result (e.g. "625B"). NOT the postal code.
    """
    params = {
        "postalcode": postalcode,
        "hbn": blk_no,
    }
    return await moe_get("/api/onemap/moe/queryKindergartens", params)
