"""Application settings: one class, read once, from these sources.

Highest priority first (pydantic-settings' default order):
  1. arguments passed to Settings(...)        tests only
  2. environment variables APP_...            the deployment's values
  3. the .env file next to pyproject.toml     local development
  4. files in secrets/ (one file per value)   mounted secrets
  5. the defaults below

Copy this file to src/<package>/config.py and change the fields, the
prefix and PROJECT_DIR if the file sits at another depth.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# src/app/config.py -> parents[2] is the project folder. Anchoring the
# paths here means the working directory does not matter.
PROJECT_DIR = Path(__file__).resolve().parents[2]
SECRETS_DIR = PROJECT_DIR / "secrets"


class DatabaseSettings(BaseModel):
    host: str = "localhost"
    port: int = 5432
    name: str = "app"
    user: str = "app"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=PROJECT_DIR / ".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",          # APP_DB__HOST -> db.host
        # A missing secrets directory only warns; skip it when absent.
        secrets_dir=SECRETS_DIR if SECRETS_DIR.is_dir() else None,
        # Keys in .env without APP_ belong to other tools and are ignored;
        # an APP_ key that matches no field still fails (a typo).
        # Needs pydantic-settings 2.14; on older versions use extra="ignore".
        dotenv_filtering="match_prefix",
    )

    environment: Literal["dev", "test", "prod"] = "dev"
    port: int = 8000
    log_level: Literal["debug", "info", "warning", "error"] = "info"
    db: DatabaseSettings = DatabaseSettings()
    # A secret sits at the top level so that one file, secrets/app_db_password,
    # can set it: the plain secrets source does not split names on "__".
    db_password: SecretStr = SecretStr("")


@lru_cache
def get_settings() -> Settings:
    """The settings, built on first use. Tests call get_settings.cache_clear()."""
    return Settings()
