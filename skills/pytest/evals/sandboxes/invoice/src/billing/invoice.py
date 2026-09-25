import datetime

from billing.clock import today


def due_date(days: int = 30) -> datetime.date:
    """The due date of an invoice issued today."""
    return today() + datetime.timedelta(days=days)
