class Settings:
    """Settings are attached at start-up from the environment (see load)."""


settings = Settings()


def load(env):
    for key, value in env.items():
        if key.startswith("FEEDS_"):
            setattr(settings, key[6:].lower(), value)


def page_size():
    return int(settings.page_size)


def feed_title(feed):
    title = None
    for entry in feed:
        if entry.get("kind") == "title":
            title = entry["text"]
    return title.strip()
