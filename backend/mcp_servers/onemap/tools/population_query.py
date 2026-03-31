from mcp_servers.onemap.server import mcp
from mcp_servers.onemap.auth import onemap_get


async def _pop_query(endpoint: str, planningArea: str, year: str, gender: str | None = None) -> dict:
    params: dict = {"planningArea": planningArea, "year": year}
    if gender:
        params["gender"] = gender
    return await onemap_get(f"/api/public/popapi/{endpoint}", params)


@mcp.tool()
async def get_economic_status(planningArea: str, year: str, gender: str | None = None) -> dict:
    """Get economic status data (employed, unemployed, inactive) for a planning area.

    Args:
        planningArea: Planning area name (e.g. 'Bedok', 'Tampines')
        year: Census year - '2000', '2010', '2015', or '2020'
        gender: Optional - 'male' or 'female'
    """
    return await _pop_query("getEconomicStatus", planningArea, year, gender)


@mcp.tool()
async def get_education_attending(planningArea: str, year: str) -> dict:
    """Get education attendance data for a planning area.

    Args:
        planningArea: Planning area name
        year: Census year - '2000', '2010', '2015', or '2020'
    """
    return await _pop_query("getEducationAttending", planningArea, year)


@mcp.tool()
async def get_ethnic_group(planningArea: str, year: str, gender: str | None = None) -> dict:
    """Get ethnic group distribution for a planning area.

    Args:
        planningArea: Planning area name
        year: Census year - '2000', '2010', '2015', or '2020'
        gender: Optional - 'male' or 'female'
    """
    return await _pop_query("getEthnicGroup", planningArea, year, gender)


@mcp.tool()
async def get_household_monthly_income(planningArea: str, year: str) -> dict:
    """Get household monthly income from work distribution for a planning area.

    Args:
        planningArea: Planning area name
        year: Census year - '2000', '2010', '2015', or '2020'
    """
    return await _pop_query("getHouseholdMonthlyIncomeWork", planningArea, year)


@mcp.tool()
async def get_household_size(planningArea: str, year: str) -> dict:
    """Get household size distribution for a planning area.

    Args:
        planningArea: Planning area name
        year: Census year - '2000', '2010', '2015', or '2020'
    """
    return await _pop_query("getHouseholdSize", planningArea, year)


@mcp.tool()
async def get_household_structure(planningArea: str, year: str) -> dict:
    """Get household structure data for a planning area.

    Args:
        planningArea: Planning area name
        year: Census year - '2000', '2010', '2015', or '2020'
    """
    return await _pop_query("getHouseholdStructure", planningArea, year)


@mcp.tool()
async def get_income_from_work(planningArea: str, year: str) -> dict:
    """Get individual income from work distribution for a planning area.

    Args:
        planningArea: Planning area name
        year: Census year - '2000', '2010', '2015', or '2020'
    """
    return await _pop_query("getIncomeFromWork", planningArea, year)


@mcp.tool()
async def get_industry(planningArea: str, year: str) -> dict:
    """Get industry distribution (manufacturing, construction, services, etc.) for a planning area.

    Args:
        planningArea: Planning area name
        year: Census year - '2000', '2010', '2015', or '2020'
    """
    return await _pop_query("getIndustry", planningArea, year)


@mcp.tool()
async def get_language_literate(planningArea: str, year: str) -> dict:
    """Get language literacy data for a planning area.

    Args:
        planningArea: Planning area name
        year: Census year - '2000', '2010', '2015', or '2020'
    """
    return await _pop_query("getLanguageLiterate", planningArea, year)


@mcp.tool()
async def get_marital_status(planningArea: str, year: str, gender: str | None = None) -> dict:
    """Get marital status distribution for a planning area.

    Args:
        planningArea: Planning area name
        year: Census year - '2000', '2010', '2015', or '2020'
        gender: Optional - 'male' or 'female'
    """
    return await _pop_query("getMaritalStatus", planningArea, year, gender)


@mcp.tool()
async def get_mode_of_transport_school(planningArea: str, year: str) -> dict:
    """Get mode of transport to school data for a planning area.

    Args:
        planningArea: Planning area name
        year: Census year - '2000', '2010', '2015', or '2020'
    """
    return await _pop_query("getModeOfTransportSchool", planningArea, year)


@mcp.tool()
async def get_mode_of_transport_work(planningArea: str, year: str) -> dict:
    """Get mode of transport to work data for a planning area.

    Args:
        planningArea: Planning area name
        year: Census year - '2000', '2010', '2015', or '2020'
    """
    return await _pop_query("getModeOfTransportWork", planningArea, year)


@mcp.tool()
async def get_population_age_group(planningArea: str, year: str, gender: str | None = None) -> dict:
    """Get population by age group for a planning area.

    Args:
        planningArea: Planning area name
        year: Census year - '2000', '2010', '2015', or '2020'
        gender: Optional - 'male' or 'female'
    """
    return await _pop_query("getPopulationAgeGroup", planningArea, year, gender)


@mcp.tool()
async def get_religion(planningArea: str, year: str) -> dict:
    """Get religion distribution for a planning area.

    Args:
        planningArea: Planning area name
        year: Census year - '2000', '2010', '2015', or '2020'
    """
    return await _pop_query("getReligion", planningArea, year)


@mcp.tool()
async def get_spoken_at_home(planningArea: str, year: str) -> dict:
    """Get languages spoken at home data for a planning area.

    Args:
        planningArea: Planning area name
        year: Census year - '2000', '2010', '2015', or '2020'
    """
    return await _pop_query("getSpokenAtHome", planningArea, year)


@mcp.tool()
async def get_tenancy(planningArea: str, year: str) -> dict:
    """Get tenancy status (owner, tenant, others) for a planning area.

    Args:
        planningArea: Planning area name
        year: Census year - '2000', '2010', '2015', or '2020'
    """
    return await _pop_query("getTenancy", planningArea, year)


@mcp.tool()
async def get_dwelling_type_household(planningArea: str, year: str) -> dict:
    """Get type of dwelling by household for a planning area.

    Args:
        planningArea: Planning area name
        year: Census year - '2000', '2010', '2015', or '2020'
    """
    return await _pop_query("getTypeOfDwellingHousehold", planningArea, year)


@mcp.tool()
async def get_dwelling_type_population(planningArea: str, year: str) -> dict:
    """Get type of dwelling by population for a planning area.

    Args:
        planningArea: Planning area name
        year: Census year - '2000', '2010', '2015', or '2020'
    """
    return await _pop_query("getTypeOfDwellingPop", planningArea, year)
