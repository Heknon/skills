import os

SMTP_HOST = os.environ["NOTIFY_SMTP_HOST"]
TIMEOUT = float(os.environ.get("NOTIFY_TIMEOUT", "30"))
RETRIES = int(os.environ.get("NOTIFY_RETRIES", "4"))
BATCH_SIZE = int(os.getenv("NOTIFY_BATCH_SIZE", "100"))
FROM_ADDRESS = os.getenv("NOTIFY_FROM", "noreply@example.internal")
