from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BILLING_", env_file=".env")

    port: int = 8000
    currency: str = "EUR"
