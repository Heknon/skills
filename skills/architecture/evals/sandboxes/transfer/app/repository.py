from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Account
from app.errors import AccountUnavailableError, InsufficientFundsError


class AccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def balance(self, account_id: int) -> int | None:
        return await self.session.scalar(select(Account.balance_cents).where(Account.id == account_id))

    async def debit(self, account_id: int, amount_cents: int) -> None:
        result = await self.session.execute(
            update(Account)
            .where(Account.id == account_id, ~Account.frozen, Account.balance_cents >= amount_cents)
            .values(balance_cents=Account.balance_cents - amount_cents)
        )
        if result.rowcount == 0:
            raise InsufficientFundsError(account_id)
        await self.session.commit()

    async def credit(self, account_id: int, amount_cents: int) -> None:
        result = await self.session.execute(
            update(Account)
            .where(Account.id == account_id, ~Account.frozen)
            .values(balance_cents=Account.balance_cents + amount_cents)
        )
        if result.rowcount == 0:
            raise AccountUnavailableError(account_id)
        await self.session.commit()
