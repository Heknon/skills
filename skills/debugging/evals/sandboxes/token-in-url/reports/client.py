import json
import urllib.request


class ReportServiceError(Exception):
    pass


def fetch_report(base_url, api_token, report_id):
    """The report as a dict. The service takes its token as a query parameter."""
    url = f"{base_url}/v1/reports/{report_id}?token={api_token}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return json.load(response)
    except OSError:
        raise ReportServiceError("report service failed") from None
