from app.errors import CustomerNotFoundError
from app.repositories.orders import Order, OrderRepository


class OrderService:
    """Order rules. Called by the API and by the nightly import (app/worker.py)."""

    def __init__(self, repo: OrderRepository) -> None:
        self.repo = repo

    def place(self, customer_id: int, amount_cents: int) -> Order:
        customer = self.repo.get_customer(customer_id)
        if customer is None:
            raise CustomerNotFoundError(customer_id)
        return self.repo.add_order(customer_id, amount_cents)
