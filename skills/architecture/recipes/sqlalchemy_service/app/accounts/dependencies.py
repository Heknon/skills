"""Providers: the wiring from a request to a service. Tests override
get_account_service (or get_session) in app.dependency_overrides."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounts.repository import SqlUnitOfWork
from app.accounts.service import AccountService
from app.db import get_session


def get_unit_of_work(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SqlUnitOfWork:
    return SqlUnitOfWork(session)


def get_account_service(
    uow: Annotated[SqlUnitOfWork, Depends(get_unit_of_work)],
) -> AccountService:
    return AccountService(uow)


AccountServiceDep = Annotated[AccountService, Depends(get_account_service)]
