import datetime as dt

from beanie import Document, Indexed


class Order(Document):
    customer_email: str
    status: Indexed(str)
    total_cents: int
    created_at: dt.datetime

    class Settings:
        name = "orders"
