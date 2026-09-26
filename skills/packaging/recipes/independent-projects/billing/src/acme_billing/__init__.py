"""Billing service."""

from pydantic import BaseModel, validator

from acme_core import total


class Invoice(BaseModel):
    lines: list[str]

    @validator("lines")
    def not_empty(cls, value):
        if not value:
            raise ValueError("an invoice needs lines")
        return value

    def amount(self) -> str:
        return str(total(self.lines))
