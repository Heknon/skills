"""Date arithmetic."""

from datetime import date, timedelta


def add_days(day: date, days: int) -> date:
    return day + timedelta(days=days)


def is_weekend(day: date) -> bool:
    return day.weekday() >= 5
