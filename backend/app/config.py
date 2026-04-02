from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OneMap
    onemap_email: str = ""
    onemap_password: str = ""

    # URA
    ura_access_key: str = ""

    # Azure AI Foundry
    azure_ai_project_endpoint: str = ""
    model_deployment_name: str = "gpt-4o"

    # Azure Content Understanding
    azure_content_understanding_endpoint: str = ""

    # Bing Web Search (Azure AI Foundry connection)
    bing_connection_id: str = ""

    # Server
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
