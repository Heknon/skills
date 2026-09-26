"""Request and response bodies: the HTTP contract."""

from pydantic import BaseModel, ConfigDict, Field

from app.accounts.domain import Account


class AccountIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner_email: str = Field(pattern=r"^[^@\s]+@[^@\s]+$")
    kyc_reference: str = Field(min_length=1)


class AccountOut(BaseModel):
    id: int
    owner_email: str
    balance_cents: int

    @classmethod
    def from_domain(cls, account: Account) -> "AccountOut":
        return cls(
            id=account.id,
            owner_email=account.owner_email,
            balance_cents=account.balance_cents,
        )


class TransferIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: int
    target_id: int
    amount_cents: int = Field(gt=0)
