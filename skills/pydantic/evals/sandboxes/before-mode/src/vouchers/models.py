from typing import Any

from pydantic import BaseModel, field_validator


class Voucher(BaseModel):
    code: str
    percent: int

    @field_validator("code", mode="before")
    @classmethod
    def normalise(cls, v: Any) -> str:
        return v.strip().upper()
