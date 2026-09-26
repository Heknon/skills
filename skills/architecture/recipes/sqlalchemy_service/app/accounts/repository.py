"""All SQL for accounts. Returns domain models, never rows; flushes, never commits;
turns driver errors into domain errors once, here."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounts.domain import Account
from app.accounts.errors import AccountNotFoundError, DuplicateAccountError
from app.accounts.models import AccountRow


def _to_domain(row: AccountRow) -> Account:
    return Account(
        id=row.id,
        owner_email=row.owner_email,
        kyc_reference=row.kyc_reference,
        balance_cents=row.balance_cents,
    )


def _is_unique_violation(exc: IntegrityError) -> bool:
    # asyncpg: sqlstate 23505 (read in sqlalchemy/dialects/postgresql/asyncpg.py);
    # sqlite: the message (lab, aiosqlite).
    sqlstate = getattr(exc.orig, "sqlstate", None)
    return sqlstate == "23505" or "UNIQUE constraint failed" in str(exc.orig)


class SqlAccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, account_id: int, *, for_update: bool = False) -> Account:
        stmt = select(AccountRow).where(AccountRow.id == account_id)
        if for_update:
            stmt = stmt.with_for_update()  # FOR UPDATE on PostgreSQL; SQLite ignores it
        row = await self.session.scalar(stmt)
        if row is None:
            raise AccountNotFoundError(account_id)
        return _to_domain(row)

    async def add(self, owner_email: str, kyc_reference: str) -> Account:
        row = AccountRow(
            owner_email=owner_email, kyc_reference=kyc_reference, balance_cents=0
        )
        self.session.add(row)
        try:
            # the INSERT runs at flush, so its error is raised here, not at commit
            await self.session.flush()
        except IntegrityError as exc:
            if _is_unique_violation(exc):
                raise DuplicateAccountError(owner_email) from exc
            raise
        return _to_domain(row)

    async def set_balance(self, account_id: int, balance_cents: int) -> None:
        row = await self.session.get(AccountRow, account_id)
        if row is None:
            raise AccountNotFoundError(account_id)
        row.balance_cents = balance_cents
        await self.session.flush()


class SqlUnitOfWork:
    """One session and its transaction. The service says where it starts and ends."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.accounts = SqlAccountRepository(session)

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        async with self.session.begin():  # commit on exit, rollback on an exception
            yield
