from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "moe",
    instructions="MOE Singapore school finder API tools for searching addresses, kindergartens, primary schools, and secondary schools.",
)

# Import and register all tool modules
from mcp_servers.moe.tools import (  # noqa: E402, F401
    kindergartens,
    primary_schools,
    search,
    secondary_schools,
)
