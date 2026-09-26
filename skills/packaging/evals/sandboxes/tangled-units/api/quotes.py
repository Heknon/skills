from pydantic import BaseModel

from common.money import to_cents


class Quote(BaseModel):
    price: str
    quantity: int

    def total_cents(self) -> int:
        return to_cents(self.price) * self.quantity
