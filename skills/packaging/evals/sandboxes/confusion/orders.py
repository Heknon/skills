from acme_utils import slugify


def order_key(customer: str, number: int) -> str:
    """Return the storage key of an order, such as 'acme-gmbh-00042'."""
    return f"{slugify(customer)}-{number:05d}"


if __name__ == "__main__":
    print(order_key("ACME GmbH", 42))
