import fetchkit

PARTNER_URL = "https://partner-test.internal/v2/rates"


def partner_rates() -> bytes:
    return fetchkit.get(PARTNER_URL, timeout=5, headers={"Accept": "application/json"})
