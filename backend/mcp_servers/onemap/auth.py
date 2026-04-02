import asyncio
import os
import time

import httpx

BASE_URL = "https://www.onemap.gov.sg"

_token: str | None = None
_token_expiry: float = 0
_token_lock = asyncio.Lock()
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=BASE_URL,
            timeout=30.0,
        )
    return _client


async def get_token() -> str:
    """Get a valid OneMap authentication token, refreshing if expired."""
    global _token, _token_expiry

    if _token and time.time() < _token_expiry:
        return _token

    async with _token_lock:
        # Re-check after acquiring lock (another coroutine may have refreshed)
        if _token and time.time() < _token_expiry:
            return _token

        email = os.environ.get("ONEMAP_EMAIL", "")
        password = os.environ.get("ONEMAP_PASSWORD", "")

        client = _get_client()
        resp = await client.post(
            "/api/auth/post/getToken",
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
    client = _get_client()
    resp = await client.get(
        path,
        params=params,
        headers={"Authorization": token},
    )
    resp.raise_for_status()
    return resp.json()
