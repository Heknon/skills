"""Paging over the product list."""

PAGE_SIZE = 20
MAX_NAME_LENGTH = 80

PRODUCTS = [f"product-{i:03d}" for i in range(1, 121)]


def page(number: int) -> list[str]:
    start = (number - 1) * PAGE_SIZE
    return PRODUCTS[start : start + PAGE_SIZE]
