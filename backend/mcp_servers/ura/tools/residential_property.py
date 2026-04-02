from mcp_servers.ura.auth import svy21_to_wgs84, ura_get
from mcp_servers.ura.server import mcp


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


def _filter_projects(
    result: dict,
    street: str | None = None,
    project: str | None = None,
    district: str | None = None,
    max_projects: int = 20,
    max_transactions: int = 5,
) -> dict:
    """Filter and limit property results to avoid exceeding LLM context window."""
    if "Result" not in result or not isinstance(result["Result"], list):
        return result

    items = result["Result"]
    street_upper = street.strip().upper() if street else None
    project_upper = project.strip().upper() if project else None
    district_str = str(district).strip().zfill(2) if district else None

    filtered = []
    for item in items:
        if street_upper and street_upper not in (item.get("street") or "").upper():
            continue
        if project_upper and project_upper not in (item.get("project") or "").upper():
            continue
        if district_str:
            # district can be on the item or nested in transactions/rentals
            item_district = item.get("district", "")
            if item_district and str(item_district).strip().zfill(2) != district_str:
                continue
        filtered.append(item)

    # Limit nested transaction/rental arrays per project
    for item in filtered[:max_projects]:
        for key in ("transaction", "rental", "rentalMedian", "developerSales"):
            if key in item and isinstance(item[key], list):
                item[key] = item[key][:max_transactions]

    total = len(filtered)
    result["Result"] = filtered[:max_projects]
    result["_filtered"] = {
        "total_matching": total,
        "returned": len(result["Result"]),
        "filters_applied": {
            k: v
            for k, v in {
                "street": street,
                "project": project,
                "district": district,
            }.items()
            if v is not None
        },
    }
    return result


@mcp.tool()
async def get_private_resi_transactions(
    batch: int,
    street: str | None = None,
    project: str | None = None,
    district: str | None = None,
) -> dict:
    """Get private residential property transactions for the past 5 years.

    IMPORTANT: Always provide at least one filter (street, project, or district)
    to avoid exceeding the context window. Results are limited to 20 projects
    with the 5 most recent transactions each.

    Args:
        batch: Data batch number (1-4), split by postal districts.
               1 = districts 01-07, 2 = districts 08-14,
               3 = districts 15-21, 4 = districts 22-28.
        street: Filter by street name (case-insensitive partial match, e.g. 'ORCHARD')
        project: Filter by project name (case-insensitive partial match, e.g. 'THE AVENIR')
        district: Filter by postal district number (e.g. '09')

    Returns project name, street, market segment, property type, tenure,
    transaction price, area, floor range, contract date, and coordinates.
    """
    result = await ura_get("PMI_Resi_Transaction", {"batch": batch})
    result = _convert_property_coords(result)
    return _filter_projects(result, street=street, project=project, district=district)


@mcp.tool()
async def get_private_resi_median_rentals(
    street: str | None = None,
    project: str | None = None,
    district: str | None = None,
) -> dict:
    """Get median rentals of private non-landed residential properties for the past 3 years.

    IMPORTANT: Always provide at least one filter (street, project, or district)
    to avoid exceeding the context window. Results are limited to 20 projects.

    Args:
        street: Filter by street name (case-insensitive partial match)
        project: Filter by project name (case-insensitive partial match)
        district: Filter by postal district number (e.g. '15')

    Returns project name, street, district, reference period, median/25th/75th
    percentile PSF per month, and coordinates.
    """
    result = await ura_get("PMI_Resi_Rental_Median")
    result = _convert_property_coords(result)
    return _filter_projects(result, street=street, project=project, district=district)


@mcp.tool()
async def get_private_resi_rental_contracts(
    refPeriod: str,
    street: str | None = None,
    project: str | None = None,
    district: str | None = None,
) -> dict:
    """Get private residential property rental contracts for a specific quarter.

    IMPORTANT: Always provide at least one filter (street, project, or district)
    to avoid exceeding the context window. Results are limited to 20 projects.

    Args:
        refPeriod: Reference quarter in format 'yyqq' (e.g. '24q1' for 2024 Q1)
        street: Filter by street name (case-insensitive partial match)
        project: Filter by project name (case-insensitive partial match)
        district: Filter by postal district number

    Returns project name, street, district, property type, number of bedrooms,
    rent amount, floor area, lease date, and coordinates.
    """
    result = await ura_get("PMI_Resi_Rental", {"refPeriod": refPeriod})
    result = _convert_property_coords(result)
    return _filter_projects(result, street=street, project=project, district=district)


@mcp.tool()
async def get_private_resi_developer_sales(
    refPeriod: str,
    street: str | None = None,
    project: str | None = None,
    district: str | None = None,
) -> dict:
    """Get private residential units sold by developers for a specific month.

    IMPORTANT: Always provide at least one filter (street, project, or district)
    to avoid exceeding the context window. Results are limited to 20 projects.

    Args:
        refPeriod: Reference month in format 'mmyy' (e.g. '0924' for Sep 2024)
        street: Filter by street name (case-insensitive partial match)
        project: Filter by project name (case-insensitive partial match)
        district: Filter by postal district number

    Returns project name, developer, street, district, market segment,
    median/lowest/highest price PSF, units available/launched/sold.
    """
    result = await ura_get("PMI_Resi_Developer_Sales", {"refPeriod": refPeriod})
    result = _convert_property_coords(result)
    return _filter_projects(result, street=street, project=project, district=district)


@mcp.tool()
async def get_private_resi_pipeline() -> dict:
    """Get private residential projects in the pipeline for the latest quarter.

    Returns project name, street, district, developer, total units,
    unit breakdown by type (detached/semi-detached/terrace/apartment/condo),
    and expected TOP year.
    Updates quarterly (4th Friday of Jan/Apr/Jul/Oct).
    """
    return await ura_get("PMI_Resi_Pipeline")
