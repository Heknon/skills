from itertools import count

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()


class PaymentIn(BaseModel):
    account: str
    amount_cents: int = Field(gt=0)


class Payment(PaymentIn):
    id: int


PAYMENTS: dict[int, Payment] = {}
_ids = count(1)


def charge_card(account: str, amount_cents: int) -> None:
    """Calls the card processor. Money moves here; it cannot be undone."""


@app.post("/payments", status_code=201)
def create_payment(body: PaymentIn) -> Payment:
    charge_card(body.account, body.amount_cents)
    payment = Payment(id=next(_ids), **body.model_dump())
    PAYMENTS[payment.id] = payment
    return payment


@app.get("/payments")
def list_payments() -> list[Payment]:
    return list(PAYMENTS.values())
