import os

from mcp.server.transport_security import TransportSecuritySettings
from mcp_servers.ura.server import mcp

transport = os.environ.get("MCP_TRANSPORT", "stdio")

if transport == "streamable-http":
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = 8000
    mcp.settings.transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=False
    )
    mcp.run(transport="streamable-http")
else:
    mcp.run()
