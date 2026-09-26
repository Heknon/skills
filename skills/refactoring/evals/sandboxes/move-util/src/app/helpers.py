"""Small helpers shared by the importers."""

from datetime import date, datetime

DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y")


def parse_date(text: str) -> date:
    """Parse a date written in one of DATE_FORMATS; raise ValueError otherwise."""
    cleaned = text.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"unknown date format: {text!r}")


def slug(text: str) -> str:
    return "-".join(text.lower().split())
