import os

LOG_LEVEL = os.environ.get("APP_LOG_LEVEL", "info")
CACHE_TTL_SECONDS = int(os.environ.get("APP_CACHE_TTL", "300"))
