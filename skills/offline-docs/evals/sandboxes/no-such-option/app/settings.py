import quickcfg


def load_settings() -> dict:
    return quickcfg.load("settings.toml", env_prefix="BILLING")
