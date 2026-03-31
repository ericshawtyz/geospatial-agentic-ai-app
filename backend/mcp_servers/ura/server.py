from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ura", instructions="URA (Urban Redevelopment Authority) Singapore API tools for car parks, property transactions, rentals, planning decisions, and approved use data.")

# Import and register all tool modules
from mcp_servers.ura.tools import (  # noqa: E402, F401
    car_park,
    residential_property,
    planning_decisions,
    approved_use,
)


