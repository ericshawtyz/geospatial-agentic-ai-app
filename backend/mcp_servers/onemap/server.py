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
    land_lot,
)


