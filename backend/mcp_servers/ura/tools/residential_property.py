from mcp_servers.ura.server import mcp
from mcp_servers.ura.auth import ura_get, svy21_to_wgs84


def _convert_property_coords(result: dict) -> dict:
    """Convert SVY21 x/y coordinates in property results to WGS84."""
    if "Result" in result:
        for item in result["Result"]:
            x_val = item.get("x")
            y_val = item.get("y")
            if x_val and y_val:
                try:
                    lat, lng = svy21_to_wgs84(float(x_val), float(y_val))
                    item["latitude"] = lat
                    item["longitude"] = lng
                except (ValueError, TypeError):
                    pass
    return result


@mcp.tool()
async def get_private_resi_transactions(batch: int) -> dict:
    """Get private residential property transactions for the past 5 years.

    Args:
        batch: Data batch number (1-4), split by postal districts.
               1 = districts 01-07, 2 = districts 08-14,
               3 = districts 15-21, 4 = districts 22-28.

    Returns project name, street, market segment, property type, tenure,
    transaction price, area, floor range, contract date, and coordinates.
    Updates every Tuesday and Friday.
    """
    result = await ura_get("PMI_Resi_Transaction", {"batch": batch})
    return _convert_property_coords(result)


@mcp.tool()
async def get_private_resi_median_rentals() -> dict:
    """Get median rentals of private non-landed residential properties for the past 3 years.

    Returns project name, street, district, reference period, median/25th/75th
    percentile PSF per month, and coordinates. Properties must have at least 10
    rental contracts in the reference period.
    Updates quarterly (4th Friday of Jan/Apr/Jul/Oct).
    """
    result = await ura_get("PMI_Resi_Rental_Median")
    return _convert_property_coords(result)


@mcp.tool()
async def get_private_resi_rental_contracts(refPeriod: str) -> dict:
    """Get private residential property rental contracts for a specific quarter.

    Args:
        refPeriod: Reference quarter in format 'yyqq' (e.g. '24q1' for 2024 Q1)

    Returns project name, street, district, property type, number of bedrooms,
    rent amount, floor area, lease date, and coordinates.
    Updates monthly (15th of each month).
    """
    result = await ura_get("PMI_Resi_Rental", {"refPeriod": refPeriod})
    return _convert_property_coords(result)


@mcp.tool()
async def get_private_resi_developer_sales(refPeriod: str) -> dict:
    """Get private residential units sold by developers for a specific month.

    Args:
        refPeriod: Reference month in format 'mmyy' (e.g. '0924' for Sep 2024)

    Returns project name, developer, street, district, market segment,
    median/lowest/highest price PSF, units available/launched/sold.
    Updates monthly (15th of each month).
    """
    result = await ura_get("PMI_Resi_Developer_Sales", {"refPeriod": refPeriod})
    return _convert_property_coords(result)


@mcp.tool()
async def get_private_resi_pipeline() -> dict:
    """Get the pipeline of private residential projects for the latest quarter.

    Returns project name, street, district, developer, total units,
    breakdown by property type (detached/semi-detached/terrace/apartment/condo),
    and expected TOP year.
    Updates quarterly (4th Friday of Jan/Apr/Jul/Oct).
    """
    result = await ura_get("PMI_Resi_Pipeline")
    return result
