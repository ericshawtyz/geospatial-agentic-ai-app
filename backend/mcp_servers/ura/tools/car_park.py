from mcp_servers.ura.server import mcp
from mcp_servers.ura.auth import ura_get, svy21_to_wgs84


@mcp.tool()
async def get_car_park_availability() -> dict:
    """Get real-time available lots for all URA car parks in Singapore.

    Returns car park numbers, lot types (Car/Motorcycle/Heavy Vehicle),
    available lots, and coordinates in SVY21 format.
    Updates every 3-5 minutes.
    """
    result = await ura_get("Car_Park_Availability")
    # Convert SVY21 coordinates to WGS84 for map display
    if "Result" in result:
        for item in result["Result"]:
            if "geometries" in item:
                for geom in item["geometries"]:
                    coords = geom.get("coordinates", "")
                    if coords:
                        parts = coords.split(", ")
                        if len(parts) == 2:
                            try:
                                x, y = float(parts[0]), float(parts[1])
                                lat, lng = svy21_to_wgs84(x, y)
                                geom["wgs84"] = {"latitude": lat, "longitude": lng}
                            except ValueError:
                                pass
    return result


@mcp.tool()
async def get_car_park_details() -> dict:
    """Get detailed information and rates for all URA car parks.

    Returns car park names, rates (weekday/Saturday/Sunday), parking system type,
    capacity, vehicle categories, and coordinates. Updates daily.
    """
    result = await ura_get("Car_Park_Details")
    if "Result" in result:
        for item in result["Result"]:
            if "geometries" in item:
                for geom in item["geometries"]:
                    coords = geom.get("coordinates", "")
                    if coords:
                        parts = coords.split(", ")
                        if len(parts) == 2:
                            try:
                                x, y = float(parts[0]), float(parts[1])
                                lat, lng = svy21_to_wgs84(x, y)
                                geom["wgs84"] = {"latitude": lat, "longitude": lng}
                            except ValueError:
                                pass
    return result


@mcp.tool()
async def get_season_car_park_details() -> dict:
    """Get season car park details and monthly rates from URA.

    Returns car park names, monthly rates, parking hours, ticket types,
    vehicle categories, and coordinates. Updates daily.
    """
    result = await ura_get("Season_Car_Park_Details")
    if "Result" in result:
        for item in result["Result"]:
            if "geometries" in item:
                for geom in item["geometries"]:
                    coords = geom.get("coordinates", "")
                    if coords:
                        parts = coords.split(", ")
                        if len(parts) == 2:
                            try:
                                x, y = float(parts[0]), float(parts[1])
                                lat, lng = svy21_to_wgs84(x, y)
                                geom["wgs84"] = {"latitude": lat, "longitude": lng}
                            except ValueError:
                                pass
    return result
