from pydantic import BaseModel


class OrderPatch(BaseModel):
    status: str | None = None
    note: str | None = None
    quantity: int | None = None
