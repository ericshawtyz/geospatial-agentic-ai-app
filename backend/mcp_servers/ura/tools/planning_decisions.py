from mcp_servers.ura.server import mcp
from mcp_servers.ura.auth import ura_get


@mcp.tool()
async def get_planning_decisions(
    year: int | None = None, last_dnload_date: str | None = None
) -> dict:
    """Get planning decisions (Written Permission granted or rejected) from URA.

    Provide either 'year' OR 'last_dnload_date', but not both.

    Args:
        year: Year to retrieve decisions for (must be > 2000, e.g. 2024)
        last_dnload_date: Get decisions created/modified/deleted since this date.
                          Format: 'dd/mm/yyyy'. Cannot be more than 1 year ago.

    Returns submission number, decision number, decision date, decision type,
    proposal description, address, MK/TS lot number, and deletion indicator.
    Updates daily.
    """
    params: dict = {}
    if year is not None:
        params["year"] = year
    elif last_dnload_date is not None:
        params["last_dnload_date"] = last_dnload_date
    return await ura_get("Planning_Decision", params)
