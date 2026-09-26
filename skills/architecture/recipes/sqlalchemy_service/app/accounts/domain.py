"""What the service works with. No HTTP, no database."""

from pydantic import BaseModel, ConfigDict


class Account(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    owner_email: str
    kyc_reference: str  # internal: never sent to clients
    balance_cents: int
