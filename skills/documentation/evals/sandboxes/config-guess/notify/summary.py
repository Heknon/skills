from email.message import EmailMessage


def build_messages(date):
    message = EmailMessage()
    message["To"] = "owner@example.internal"
    message["Subject"] = f"Summary for {date or 'yesterday'}"
    return [message]
