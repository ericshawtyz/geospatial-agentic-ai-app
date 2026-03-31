import os
import time

import httpx

BASE_URL = "https://www.onemap.gov.sg"

_token: str | None = None
_token_expiry: float = 0


async def get_token() -> str:
    """Get a valid OneMap authentication token, refreshing if expired."""
    global _token, _token_expiry

    if _token and time.time() < _token_expiry:
        return _token

    email = os.environ.get("ONEMAP_EMAIL", "")
    password = os.environ.get("ONEMAP_PASSWORD", "")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/api/auth/post/getToken",
            json={"email": email, "password": password},
        )
        resp.raise_for_status()
        data = resp.json()

    _token = data["access_token"]
    # Token valid for 3 days; refresh 1 hour early
    _token_expiry = float(data["expiry_timestamp"]) - 3600
    return _token


async def onemap_get(path: str, params: dict | None = None) -> dict:
    """Make an authenticated GET request to the OneMap API."""
    token = await get_token()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}{path}",
            params=params,
            headers={"Authorization": token},
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()
