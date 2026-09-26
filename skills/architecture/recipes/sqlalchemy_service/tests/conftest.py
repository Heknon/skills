import copy
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest

from app.accounts.domain import Account
from app.accounts.errors import AccountNotFoundError, DuplicateAccountError


class FakeAccounts:
    """The repository contract (domain models in, domain errors out), in a dict."""

    def __init__(self) -> None:
        self.rows: dict[int, Account] = {}
        self.broken: set[int] = (
            set()
        )  # set_balance on these fails, like a lost connection

    async def get(self, account_id: int, *, for_update: bool = False) -> Account:
        if account_id not in self.rows:
            raise AccountNotFoundError(account_id)
        return self.rows[account_id]

    async def add(self, owner_email: str, kyc_reference: str) -> Account:
        if any(a.owner_email == owner_email for a in self.rows.values()):
            raise DuplicateAccountError(owner_email)
        account = Account(
            id=len(self.rows) + 1,
            owner_email=owner_email,
            kyc_reference=kyc_reference,
            balance_cents=0,
        )
        self.rows[account.id] = account
        return account

    async def set_balance(self, account_id: int, balance_cents: int) -> None:
        if account_id in self.broken:
            msg = "database went away"
            raise ConnectionError(msg)
        account = await self.get(account_id)
        self.rows[account_id] = account.model_copy(
            update={"balance_cents": balance_cents}
        )


class FakeUnitOfWork:
    """Rolls back like a database: the rows are restored when the block raises."""

    def __init__(self) -> None:
        self.accounts = FakeAccounts()
        self.commits = 0

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        saved = copy.deepcopy(self.accounts.rows)
        try:
            yield
        except BaseException:
            self.accounts.rows = saved
            raise
        self.commits += 1


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()
