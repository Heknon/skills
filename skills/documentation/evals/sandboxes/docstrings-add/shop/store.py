"""Read products from the warehouse."""
import warehouse_client


def load(category: str) -> list[dict]:
    """Load the products in a category."""
    return warehouse_client.fetch("products", category=category)


def poll(sku: str, timeout: float) -> bool:
    return warehouse_client.wait_until_available(sku, timeout)
