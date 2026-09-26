import fetchkit

RATES_URL = "https://rates.internal/v1/daily"


def load_rates() -> bytes:
    return fetchkit.get(RATES_URL)
