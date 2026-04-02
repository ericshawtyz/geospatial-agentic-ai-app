import httpx

BASE_URL = "https://www.moe.gov.sg"

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=30.0,
        )
    return _client


async def moe_get(path: str, params: dict | None = None) -> dict:
    """Make a GET request to the MOE API."""
    client = _get_client()
    resp = await client.get(path, params=params)
    resp.raise_for_status()
    return resp.json()
