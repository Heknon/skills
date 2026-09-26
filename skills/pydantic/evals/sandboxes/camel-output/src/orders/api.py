from orders.schemas import OrderOut


def order_response(order: OrderOut) -> str:
    """The JSON body returned by GET /orders/{id}."""
    return order.model_dump_json()
