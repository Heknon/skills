from pydantic import BaseModel, ConfigDict, Field


class Payment(BaseModel):
    """A payment as the payment provider sends and expects it (camelCase)."""

    model_config = ConfigDict(populate_by_name=True)

    amount_cents: int = Field(alias="amountCents")
    currency: str
