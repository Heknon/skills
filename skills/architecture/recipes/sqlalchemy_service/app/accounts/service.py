"""Account rules. Called by the API; a worker or CLI can call it the same way."""

from contextlib import AbstractAsyncContextManager
from typing import Protocol

from app.accounts.domain import Account
from app.accounts.errors import InsufficientFundsError


class AccountRepository(Protocol):
    async def get(self, account_id: int, *, for_update: bool = False) -> Account: ...
    async def add(self, owner_email: str, kyc_reference: str) -> Account: ...
    async def set_balance(self, account_id: int, balance_cents: int) -> None: ...


class UnitOfWork(Protocol):
    accounts: AccountRepository

    def transaction(self) -> AbstractAsyncContextManager[None]: ...


class AccountService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def open_account(self, owner_email: str, kyc_reference: str) -> Account:
        async with self.uow.transaction():
            return await self.uow.accounts.add(owner_email, kyc_reference)

    async def get(self, account_id: int) -> Account:
        async with self.uow.transaction():
            return await self.uow.accounts.get(account_id)

    async def transfer(self, source_id: int, target_id: int, amount_cents: int) -> None:
        async with self.uow.transaction():
            source = await self.uow.accounts.get(source_id, for_update=True)
            target = await self.uow.accounts.get(target_id, for_update=True)
            if source.balance_cents < amount_cents:
                raise InsufficientFundsError(
                    source_id, source.balance_cents, amount_cents
                )
            await self.uow.accounts.set_balance(
                source_id, source.balance_cents - amount_cents
            )
            await self.uow.accounts.set_balance(
                target_id, target.balance_cents + amount_cents
            )
