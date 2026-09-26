import datetime as dt

from beanie import Document, Indexed, Link


class Customer(Document):
    name: str
    country: str

    class Settings:
        name = "customers"


class Order(Document):
    customer: Link[Customer]
    status: Indexed(str)
    total_cents: int
    created_at: dt.datetime

    class Settings:
        name = "orders"
