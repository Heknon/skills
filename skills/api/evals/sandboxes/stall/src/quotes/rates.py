"""Client for the legacy rates service.

In production this makes a blocking HTTP call with a synchronous client.
Here the call is simulated with time.sleep so the project runs offline.
"""

import time

LATENCY_SECONDS = 0.5
_RATES = {"EUR": 1.0, "USD": 1.08, "GBP": 0.85}


def fetch_rate(currency: str) -> float:
    time.sleep(LATENCY_SECONDS)  # stands for: requests.get(f"{RATES_URL}/{currency}").json()
    return _RATES[currency]
