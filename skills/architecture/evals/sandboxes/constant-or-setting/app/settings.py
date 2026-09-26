from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CATALOGUE_")

    database_url: str = "sqlite:///catalogue.db"
    request_timeout_s: float = 5.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
