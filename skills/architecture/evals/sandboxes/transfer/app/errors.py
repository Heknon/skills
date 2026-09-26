class AccountUnavailableError(Exception):
    """The account does not exist or is frozen."""

    def __init__(self, account_id: int) -> None:
        super().__init__(account_id)
        self.account_id = account_id

    def __str__(self) -> str:
        return f"account {self.account_id} is missing or frozen"


class InsufficientFundsError(Exception):
    def __init__(self, account_id: int) -> None:
        super().__init__(account_id)
        self.account_id = account_id

    def __str__(self) -> str:
        return f"account {self.account_id} has insufficient funds"
