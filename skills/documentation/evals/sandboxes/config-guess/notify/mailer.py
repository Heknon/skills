import smtplib
import time

from notify import settings


def send_all(messages):
    for start in range(0, len(messages), settings.BATCH_SIZE):
        batch = messages[start:start + settings.BATCH_SIZE]
        _send_batch(batch)


def _send_batch(batch):
    for attempt in range(settings.RETRIES + 1):
        try:
            with smtplib.SMTP(settings.SMTP_HOST, timeout=settings.TIMEOUT) as smtp:
                for message in batch:
                    message["From"] = settings.FROM_ADDRESS
                    smtp.send_message(message)
            return
        except smtplib.SMTPServerDisconnected:
            time.sleep(2 ** attempt)
    raise RuntimeError("SMTP server kept disconnecting")
