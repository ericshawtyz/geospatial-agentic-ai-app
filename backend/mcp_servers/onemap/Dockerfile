FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt constraints.txt ./
RUN pip install --no-cache-dir -c constraints.txt -r requirements.txt

COPY mcp_servers/ mcp_servers/

ENV MCP_TRANSPORT=streamable-http

EXPOSE 8000

CMD ["python", "-m", "mcp_servers.onemap"]
