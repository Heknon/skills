from pydantic import BaseModel


class Row(BaseModel):
    region: str
    amount: float
