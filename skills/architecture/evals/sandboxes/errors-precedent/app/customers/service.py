from app.customers.errors import CustomerNotFoundError

CUSTOMERS = {1: {"id": 1, "name": "Ada"}}


def get_customer(customer_id: int) -> dict:
    customer = CUSTOMERS.get(customer_id)
    if customer is None:
        raise CustomerNotFoundError(customer_id)
    return customer
