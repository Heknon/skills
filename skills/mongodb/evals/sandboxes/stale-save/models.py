from pydantic import BaseModel

from beanie import Document


class Address(BaseModel):
    street: str
    city: str
    zip: str


class Customer(Document):
    name: str
    email: str
    address: Address
    loyalty_points: int = 0

    class Settings:
        name = "customers"
