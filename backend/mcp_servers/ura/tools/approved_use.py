from mcp_servers.ura.server import mcp
from mcp_servers.ura.auth import ura_get


@mcp.tool()
async def check_approved_residential_use(
    blkHouseNo: str,
    street: str,
    storeyNo: str | None = None,
    unitNo: str | None = None,
) -> dict:
    """Check if an address is approved for residential use by URA.

    Only covers private residential units (excludes HDB, State Properties,
    shophouses). Only includes completed developments with TOP.

    Args:
        blkHouseNo: Block or house number of the address
        street: Street name of the address
        storeyNo: Storey/floor number (optional)
        unitNo: Unit number (optional)

    Returns 'Y' if approved for residential use, 'NA' otherwise.
    Updates quarterly.
    """
    params: dict = {"blkHouseNo": blkHouseNo, "street": street}
    if storeyNo:
        params["storeyNo"] = storeyNo
    if unitNo:
        params["unitNo"] = unitNo
    return await ura_get("EAU_Appr_Resi_Use", params)
