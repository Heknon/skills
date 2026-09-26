from callagain import retry_call

from app.partner import fetch_rates


def nightly_rates():
    # The partner API drops about one call in five; retry_call covers it.
    return retry_call(fetch_rates, "EUR")
