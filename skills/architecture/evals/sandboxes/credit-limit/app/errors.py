"""This service's errors. main.py maps each category to an HTTP status."""


class AppError(Exception):
    """Base of every error this service raises on purpose."""


class NotFoundError(AppError):
    """Something the caller named does not exist (404)."""


class CustomerNotFoundError(NotFoundError):
    def __init__(self, customer_id: int) -> None:
        super().__init__(customer_id)
        self.customer_id = customer_id

    def __str__(self) -> str:
        return f"customer {self.customer_id} not found"
