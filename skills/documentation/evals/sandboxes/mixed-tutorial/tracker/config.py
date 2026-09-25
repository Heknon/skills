import os

PORT = int(os.getenv("TRACKER_PORT", "8000"))
HOST = os.getenv("TRACKER_HOST", "127.0.0.1")
DB_PATH = os.getenv("TRACKER_DB", "tracker.sqlite3")
LOG_LEVEL = os.getenv("TRACKER_LOG_LEVEL", "INFO")
PAGE_SIZE = int(os.getenv("TRACKER_PAGE_SIZE", "50"))
