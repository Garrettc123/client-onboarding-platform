"""Application settings loaded from environment."""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: List[str] = ["*"]

    supabase_url: str = ""
    supabase_service_key: str = ""
    database_url: str = ""

    pipedrive_webhook_secret: str = ""
    pipedrive_api_token: str = ""

    github_token: str = ""
    github_org: str = ""

    clickup_api_token: str = ""
    clickup_team_id: str = ""

    railway_token: str = ""
    railway_service_id: str = ""

    notion_token: str = ""
    notion_deploy_page_id: str = ""
    linear_api_key: str = ""
    linear_team_id: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
