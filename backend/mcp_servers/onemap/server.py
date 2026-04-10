import importlib

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("onemap", instructions="OneMap Singapore geospatial API tools for search, routing, planning areas, population data, and more.")

# Import and register all tool modules
from mcp_servers.onemap.tools import (  # noqa: E402, F401
    search,
    reverse_geocode,
    routing,
    coordinate_converter,
    themes,
    nearby_transport,
    planning_area,
    population_query,
    static_map,
)

# Optional tool modules (loaded only if present locally)
_optional_tools = ["mcp_servers.onemap.tools.land_lot"]
for _mod in _optional_tools:
    try:
        importlib.import_module(_mod)
    except ModuleNotFoundError:
        pass


