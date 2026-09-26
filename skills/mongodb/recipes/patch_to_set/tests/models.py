from pydantic import BaseModel, Field, field_validator


class Address(BaseModel):
    street: str
    city: str
    zip: str


class Customer(BaseModel):
    name: str
    email: str | None = None
    address: Address
    billing: Address | None = None
    tags: list[str] = []
    prefs: dict[str, str] = {}
    display: str | None = Field(default=None, alias="displayName")
    rev: int = 1

    @field_validator("name")
    @classmethod
    def tidy(cls, v: str) -> str:
        return " ".join(v.split())
