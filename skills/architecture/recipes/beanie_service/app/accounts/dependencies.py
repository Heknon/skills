"""Providers: the wiring from a request to a service. Tests override
get_account_service in app.dependency_overrides."""

from typing import Annotated

from fastapi import Depends
from pymongo import AsyncMongoClient

from app.accounts.repository import MongoUnitOfWork
from app.accounts.service import AccountService
from app.db import get_client


def get_unit_of_work(
    client: Annotated[AsyncMongoClient, Depends(get_client)],
) -> MongoUnitOfWork:
    return MongoUnitOfWork(client)


def get_account_service(
    uow: Annotated[MongoUnitOfWork, Depends(get_unit_of_work)],
) -> AccountService:
    return AccountService(uow)


AccountServiceDep = Annotated[AccountService, Depends(get_account_service)]
