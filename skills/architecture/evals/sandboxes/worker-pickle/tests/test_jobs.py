import pytest

from app import queue
from app.errors import QuotaExceededError
from app.jobs import export_rows


def test_export_within_quota():
    assert queue.run(export_rows, "acme", 50) == "exported 50 rows for acme"


def test_quota_error_reaches_the_caller():
    with pytest.raises(QuotaExceededError) as info:
        queue.run(export_rows, "acme", 500)
    assert (info.value.tenant, info.value.limit) == ("acme", 100)
    assert str(info.value) == "tenant acme is over its export quota of 100 rows"
