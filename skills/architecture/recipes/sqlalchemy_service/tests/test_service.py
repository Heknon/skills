"""The rules, with a fake unit of work: no database, no HTTP."""

import asyncio

import pytest

from app.accounts.errors import AccountNotFoundError, InsufficientFundsError
from app.accounts.service import AccountService


def funded(uow, *balances):
    service = AccountService(uow)
    for i, cents in enumerate(balances, start=1):
        account = asyncio.run(service.open_account(f"owner{i}@example.com", f"KYC-{i}"))
        asyncio.run(uow.accounts.set_balance(account.id, cents))
    return service


def test_transfer_moves_money(uow):
    service = funded(uow, 10_000, 0)
    asyncio.run(service.transfer(1, 2, 2_500))
    assert [uow.accounts.rows[i].balance_cents for i in (1, 2)] == [7_500, 2_500]


def test_insufficient_funds_changes_nothing(uow):
    service = funded(uow, 100, 0)
    with pytest.raises(InsufficientFundsError) as info:
        asyncio.run(service.transfer(1, 2, 500))
    assert (info.value.balance_cents, info.value.amount_cents) == (100, 500)
    assert [uow.accounts.rows[i].balance_cents for i in (1, 2)] == [100, 0]


def test_unknown_target_changes_nothing(uow):
    service = funded(uow, 10_000)
    with pytest.raises(AccountNotFoundError):
        asyncio.run(service.transfer(1, 99, 500))
    assert uow.accounts.rows[1].balance_cents == 10_000


def test_failed_second_write_undoes_the_first(uow):
    service = funded(uow, 10_000, 0)
    uow.accounts.broken.add(2)
    with pytest.raises(ConnectionError):
        asyncio.run(service.transfer(1, 2, 2_500))
    assert uow.accounts.rows[1].balance_cents == 10_000
