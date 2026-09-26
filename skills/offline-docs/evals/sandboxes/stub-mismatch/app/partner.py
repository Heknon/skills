import fetchkit

PARTNER_URL = "https://partner.internal/v2/rates"


def partner_rates() -> bytes:
    return fetchkit.get(PARTNER_URL, timeout=5)
