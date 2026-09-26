from app.repositories.orders import Customer, OrderRepository
from app.services.orders import OrderService
from app.worker import import_orders


def test_import_skips_unknown_customers():
    repo = OrderRepository(customers={1: Customer(id=1, credit_limit_cents=10_000)})
    report = import_orders(OrderService(repo), [
        {"customer_id": 1, "amount_cents": 100},
        {"customer_id": 9, "amount_cents": 100},
        {"customer_id": 1, "amount_cents": 200},
    ])
    assert report.placed == 2
    assert report.rejected == ["customer 9 not found"]
