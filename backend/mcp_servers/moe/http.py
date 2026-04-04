import httpx

BASE_URL = "https://www.moe.gov.sg"

_client: httpx.AsyncClient | None = None

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.moe.gov.sg/schoolfinder",
    "Origin": "https://www.moe.gov.sg",
}


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers=_HEADERS,
            timeout=30.0,
        )
    return _client


async def moe_get(path: str, params: dict | None = None) -> dict:
    """Make a GET request to the MOE API."""
    client = _get_client()
    resp = await client.get(path, params=params)
    resp.raise_for_status()
    return resp.json()
