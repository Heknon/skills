import pytest

from reports.client import ReportServiceError, fetch_report


def test_unreachable_service_raises_report_service_error():
    with pytest.raises(ReportServiceError):
        fetch_report("http://127.0.0.1:9", "test-token", "daily-sales")
