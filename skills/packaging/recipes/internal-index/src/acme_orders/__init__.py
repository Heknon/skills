"""Order keys and totals."""


def order_key(customer: str, number: int) -> str:
    return f"{customer.lower().replace(' ', '-')}-{number:05d}"
