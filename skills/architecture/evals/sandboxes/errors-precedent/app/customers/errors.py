from app.core.errors import NotFoundError


class CustomerNotFoundError(NotFoundError):
    code = "customer_not_found"

    def __init__(self, customer_id: int) -> None:
        super().__init__(customer_id)
        self.customer_id = customer_id

    def __str__(self) -> str:
        return f"customer {self.customer_id} not found"
