from shop.customers import Customer
from shop.orders import Order


def test_order_with_customer():
    order = Order.model_validate({"id": 1, "customer": {"name": "Ann"}})
    assert order.customer is not None
    assert order.customer.name == "Ann"


def test_customer_with_orders():
    customer = Customer.model_validate({"name": "Ann", "orders": [{"id": 1}, {"id": 2}]})
    assert [o.id for o in customer.orders] == [1, 2]
