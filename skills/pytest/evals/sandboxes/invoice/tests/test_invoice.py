import datetime

from billing import invoice


def test_due_date(monkeypatch):
    monkeypatch.setattr("billing.clock.today", lambda: datetime.date(2026, 1, 31))
    assert invoice.due_date() == datetime.date(2026, 3, 2)
