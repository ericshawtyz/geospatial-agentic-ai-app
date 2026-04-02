import math

from mcp_servers.ura.auth import svy21_to_wgs84, ura_get
from mcp_servers.ura.server import mcp


def _convert_carpark_coords(result: dict) -> dict:
    """Convert SVY21 coordinates in car park geometries to WGS84."""
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


def _filter_carparks_by_location(
    result: dict,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float = 1.0,
    max_results: int = 30,
) -> dict:
    """Filter car parks by proximity to a location. Must call _convert_carpark_coords first."""
    if "Result" not in result or latitude is None or longitude is None:
        # No location filter — just limit results
        if "Result" in result:
            total = len(result["Result"])
            result["Result"] = result["Result"][:max_results]
            result["_filtered"] = {"total": total, "returned": len(result["Result"])}
        return result

    def _haversine(lat1, lon1, lat2, lon2):
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    nearby = []
    for item in result.get("Result", []):
        for geom in item.get("geometries", []):
            wgs = geom.get("wgs84")
            if wgs:
                dist = _haversine(
                    latitude, longitude, wgs["latitude"], wgs["longitude"]
                )
                if dist <= radius_km:
                    item["_distance_km"] = round(dist, 3)
                    nearby.append(item)
                    break

    nearby.sort(key=lambda x: x.get("_distance_km", 999))
    result["Result"] = nearby[:max_results]
    result["_filtered"] = {
        "total_nearby": len(nearby),
        "returned": len(result["Result"]),
        "radius_km": radius_km,
    }
    return result


@mcp.tool()
async def get_car_park_availability(
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float = 1.0,
) -> dict:
    """Get real-time available lots for URA car parks in Singapore.

    IMPORTANT: Provide latitude/longitude to find car parks near a location.
    Without coordinates, only the first 30 results are returned.

    Args:
        latitude: WGS84 latitude to search near (e.g. 1.3025)
        longitude: WGS84 longitude to search near (e.g. 103.8368)
        radius_km: Search radius in km (default 1.0, max 5.0)

    Returns car park numbers, lot types (Car/Motorcycle/Heavy Vehicle),
    available lots, and coordinates. Updates every 3-5 minutes.
    """
    result = await ura_get("Car_Park_Availability")
    result = _convert_carpark_coords(result)
    return _filter_carparks_by_location(
        result, latitude, longitude, min(radius_km, 5.0)
    )


@mcp.tool()
async def get_car_park_details(
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float = 1.0,
) -> dict:
    """Get detailed information and rates for URA car parks.

    IMPORTANT: Provide latitude/longitude to find car parks near a location.
    Without coordinates, only the first 30 results are returned.

    Args:
        latitude: WGS84 latitude to search near
        longitude: WGS84 longitude to search near
        radius_km: Search radius in km (default 1.0, max 5.0)

    Returns car park names, rates (weekday/Saturday/Sunday), parking system type,
    capacity, vehicle categories, and coordinates. Updates daily.
    """
    result = await ura_get("Car_Park_Details")
    result = _convert_carpark_coords(result)
    return _filter_carparks_by_location(
        result, latitude, longitude, min(radius_km, 5.0)
    )


@mcp.tool()
async def get_season_car_park_details(
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float = 1.0,
) -> dict:
    """Get season car park details and monthly rates from URA.

    IMPORTANT: Provide latitude/longitude to find car parks near a location.
    Without coordinates, only the first 30 results are returned.

    Args:
        latitude: WGS84 latitude to search near
        longitude: WGS84 longitude to search near
        radius_km: Search radius in km (default 1.0, max 5.0)

    Returns car park names, monthly rates, parking hours, ticket types,
    vehicle categories, and coordinates. Updates daily.
    """
    result = await ura_get("Season_Car_Park_Details")
    result = _convert_carpark_coords(result)
    return _filter_carparks_by_location(
        result, latitude, longitude, min(radius_km, 5.0)
    )
    return _filter_carparks_by_location(
        result, latitude, longitude, min(radius_km, 5.0)
    )
