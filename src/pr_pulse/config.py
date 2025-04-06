from functools import lru_cache

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    github_token: str | None = None
    genai_api_key: str | None = None
    slack_webhook_url: str | None = None
    verbose: bool = False


@lru_cache
def get_config() -> Config:
    return Config()
