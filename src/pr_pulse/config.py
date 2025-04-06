from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    github_token: Optional[str] = Field(
        None, description="GitHub token for repository access"
    )
    genai_api_key: Optional[str] = Field(
        None, description="GEMINI API key to generate insights summary"
    )
    slack_webhook_url: Optional[str] = Field(
        None, description="Slack webhook URL to share insights"
    )
    verbose: bool = Field(False, description="Show detailed progress logs")
    file_prefix: str = Field("pr-pulse", description="Prefix for output files")


@lru_cache
def get_config() -> Config:
    return Config()
