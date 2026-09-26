import tomllib
from dataclasses import dataclass
from pathlib import Path


class ConfigError(Exception):
    pass


@dataclass
class Settings:
    name: str
    log_dir: Path
    timeout: int


def load(path="settings.toml"):
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        app = data["app"]
        return Settings(app["name"], Path(app["log_dir"]), int(app["timeout"]))
    except Exception:
        raise ConfigError("invalid config") from None
