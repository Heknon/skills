"""Errors of the accounts feature. Fields are positional and passed to
super().__init__ so the errors pickle; the message is built in __str__."""

from app.errors import ConflictError, NotFoundError


class AccountNotFoundError(NotFoundError):
    code = "account_not_found"

    def __init__(self, account_id: int) -> None:
        super().__init__(account_id)
        self.account_id = account_id

    def __str__(self) -> str:
        return f"account {self.account_id} not found"


class DuplicateAccountError(ConflictError):
    code = "duplicate_account"

    def __init__(self, owner_email: str) -> None:
        super().__init__(owner_email)
        self.owner_email = owner_email

    def __str__(self) -> str:
        return "an account for this owner already exists"  # no email in logs


class InsufficientFundsError(ConflictError):
    code = "insufficient_funds"

    def __init__(self, account_id: int, balance_cents: int, amount_cents: int) -> None:
        super().__init__(account_id, balance_cents, amount_cents)
        self.account_id = account_id
        self.balance_cents = balance_cents
        self.amount_cents = amount_cents

    def __str__(self) -> str:
        return (
            f"account {self.account_id} holds {self.balance_cents} cents, "
            f"cannot send {self.amount_cents}"
        )
