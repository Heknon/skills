import datetime as dt

from pydantic import BaseModel


class InvoiceIn(BaseModel):
    number: str
    customer_id: str
    amount_cents: int
    due: dt.date


class InvoiceOut(BaseModel):
    number: str
    customer_id: str
    amount_cents: int
    due: dt.date
    paid: bool
