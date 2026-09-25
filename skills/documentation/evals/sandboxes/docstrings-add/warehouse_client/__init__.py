"""Client for the warehouse service. Vendored from the platform team."""
from warehouse_client import _http


def fetch(kind, **params):
    return _http.get(f"/{kind}", params)


def wait_until_available(sku, timeout):
    return _http.get(f"/stock/{sku}/wait", {"t": timeout}).get("available", False)
