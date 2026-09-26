from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="API_", env_file=".env", secrets_dir="secrets")

    port: int = 8000
    log_level: str = "info"
    db_password: SecretStr

    @classmethod
    def settings_customise_sources(
        cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings
    ):
        # Mounted secrets are the source of truth in the cluster.
        return init_settings, file_secret_settings, env_settings, dotenv_settings
