from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OneMap
    onemap_email: str = ""
    onemap_password: str = ""

    # URA
    ura_access_key: str = ""

    # Azure AI Foundry
    azure_ai_project_endpoint: str = ""
    model_deployment_name: str = "gpt-5.4-mini"

    # Agent runtime selection.
    # - "chat_completion" (default, dev/local): runs the agent in-process via
    #   OpenAI Chat Completions over the Foundry project's OpenAI-compatible
    #   endpoint; MCP tools run locally (stdio) unless their *_MCP_URL is set.
    # - "foundry_agent_service" (prod / Container Apps): upserts a hosted
    #   agent in Azure AI Foundry Agent Service that calls the deployed MCP
    #   Container Apps directly. Requires onemap_mcp_url, ura_mcp_url, and
    #   moe_mcp_url to all be set.
    agent_mode: Literal["chat_completion", "foundry_agent_service"] = (
        "chat_completion"
    )
    # Name of the hosted agent created/updated in Foundry Agent Service when
    # agent_mode == "foundry_agent_service". Reused (upserted) on each restart.
    foundry_agent_name: str = "geo-agent"

    # Azure Content Understanding
    azure_content_understanding_endpoint: str = ""

    # Bing Web Search (Azure AI Foundry connection)
    bing_connection_id: str = ""

    # MCP Server URLs (set for container deployment; empty = local stdio mode)
    onemap_mcp_url: str = ""
    ura_mcp_url: str = ""
    moe_mcp_url: str = ""

    # Server
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
