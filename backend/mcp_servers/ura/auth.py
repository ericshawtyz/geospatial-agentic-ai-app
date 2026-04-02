import asyncio
import os
import time

import httpx

BASE_URL = "https://eservice.ura.gov.sg"

_token: str | None = None
_token_expiry: float = 0
_token_lock = asyncio.Lock()
_client: httpx.AsyncClient | None = None


def _access_key() -> str:
    return os.environ.get("URA_ACCESS_KEY", "")


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=30.0,
        )
    return _client


async def get_token() -> str:
    """Get a valid URA API token, refreshing daily."""
    global _token, _token_expiry

    if _token and time.time() < _token_expiry:
        return _token

    async with _token_lock:
        # Re-check after acquiring lock
        if _token and time.time() < _token_expiry:
            return _token

        client = _get_client()
        resp = await client.get(
            "/uraDataService/insertNewToken/v1",
            headers={"AccessKey": _access_key()},
        )
        resp.raise_for_status()
        data = resp.json()

        _token = data["Result"]
        # Token valid for 1 day; refresh after 20 hours
        _token_expiry = time.time() + 20 * 3600
        return _token


async def ura_get(service: str, params: dict | None = None) -> dict:
    """Make an authenticated GET request to the URA Data Service API."""
    token = await get_token()
    query: dict = {"service": service}
    if params:
        query.update(params)
    client = _get_client()
    resp = await client.get(
        "/uraDataService/invokeUraDS/v1",
        params=query,
        headers={
            "AccessKey": _access_key(),
            "Token": token,
        },
    )
    resp.raise_for_status()
    return resp.json()


def svy21_to_wgs84(x: float, y: float) -> tuple[float, float]:
    """Convert SVY21 (EPSG:3414) coordinates to WGS84 (lat, lng).

    Uses the standard SVY21 projection parameters for Singapore.
    """
    import math

    # SVY21 projection parameters
    a = 6378137.0  # WGS84 semi-major axis
    f = 1 / 298.257223563  # WGS84 flattening
    oLat = 1.366666666666667  # Origin latitude (degrees)
    oLon = 103.8333333333333  # Origin longitude (degrees)
    No = 38744.572  # False northing
    Eo = 28001.642  # False easting
    k = 1.0  # Scale factor

    b = a * (1 - f)
    e2 = (2 * f) - (f * f)
    e4 = e2 * e2
    e6 = e4 * e2
    A0 = 1 - (e2 / 4) - (3 * e4 / 64) - (5 * e6 / 256)
    A2 = (3.0 / 8.0) * (e2 + (e4 / 4) + (15 * e6 / 128))
    A4 = (15.0 / 256.0) * (e4 + (3 * e6 / 4))
    A6 = 35 * e6 / 3072

    lat_rad = math.radians(oLat)
    M0 = a * (
        A0 * lat_rad
        - A2 * math.sin(2 * lat_rad)
        + A4 * math.sin(4 * lat_rad)
        - A6 * math.sin(6 * lat_rad)
    )

    N_shift = y - No
    E_shift = x - Eo
    M_prime = M0 + N_shift / k

    n = (a - b) / (a + b)
    n2 = n * n
    n3 = n2 * n
    n4 = n2 * n2

    sigma = (M_prime / (a * (1 + n2 / 4 + n4 / 64))) * (1 + n2 / 4 + n4 / 64)
    lat_prime = (
        sigma
        + (3 * n / 2 - 27 * n3 / 32) * math.sin(2 * sigma)
        + (21 * n2 / 16 - 55 * n4 / 32) * math.sin(4 * sigma)
        + (151 * n3 / 96) * math.sin(6 * sigma)
        + (1097 * n4 / 512) * math.sin(8 * sigma)
    )

    sin_lat = math.sin(lat_prime)
    cos_lat = math.cos(lat_prime)
    tan_lat = math.tan(lat_prime)
    sec_lat = 1.0 / cos_lat

    rho = a * (1 - e2) / math.pow(1 - e2 * sin_lat * sin_lat, 1.5)
    nu = a / math.sqrt(1 - e2 * sin_lat * sin_lat)

    t = tan_lat
    t2 = t * t
    t4 = t2 * t2
    t6 = t4 * t2

    psi = nu / rho
    psi2 = psi * psi
    psi3 = psi2 * psi
    psi4 = psi2 * psi2

    x_nu = E_shift / (k * nu)
    x_nu2 = x_nu * x_nu
    x_nu3 = x_nu2 * x_nu
    x_nu5 = x_nu3 * x_nu2
    x_nu7 = x_nu5 * x_nu2

    # Latitude
    term1 = x_nu2 * t / (2 * rho * nu)
    term2 = (
        x_nu2
        * x_nu2
        * t
        / (24 * rho * nu * nu * nu)
        * (5 + 3 * t2 + psi - 9 * t2 * psi)
    )
    term3 = (
        x_nu2
        * x_nu2
        * x_nu2
        * t
        / (720 * rho * math.pow(nu, 5))
        * (61 + 90 * t2 + 45 * t4)
    )

    lat = lat_prime - term1 + term2 - term3

    # Longitude
    term1_lon = x_nu * sec_lat
    term2_lon = x_nu3 * sec_lat / 6 * (psi + 2 * t2)
    term3_lon = (
        x_nu5
        * sec_lat
        / 120
        * (-4 * psi3 * (1 - 6 * t2) + psi2 * (9 - 68 * t2) + 72 * psi * t2 + 24 * t4)
    )
    term4_lon = x_nu7 * sec_lat / 5040 * (61 + 662 * t2 + 1320 * t4 + 720 * t6)

    lon = math.radians(oLon) + term1_lon - term2_lon + term3_lon - term4_lon

    return (math.degrees(lat), math.degrees(lon))
