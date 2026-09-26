import datetime as dt

from beanie import Document
from pymongo import IndexModel


class Invoice(Document):
    number: str
    customer_id: str
    amount_cents: int
    due: dt.date
    paid: bool = False

    class Settings:
        name = "invoices"
        indexes = [IndexModel("number", unique=True)]
