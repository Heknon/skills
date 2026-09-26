import os


def format_banner(user: str) -> str:
    return f"Welcome back, {user}!"


def banner() -> str:
    """Return the login banner for the current user.

    The user comes from the APP_USER environment variable. When it is not
    set, the banner greets "guest".
    """
    user = os.environ.get("APP_USER")
    return format_banner(user)
