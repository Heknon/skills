import fetchkit

CATALOGUE_URL = "https://catalogue.internal/v1/items"


def load_page(page: int) -> bytes:
    return fetchkit.get(CATALOGUE_URL, 5, params={"page": str(page)})
