"""All MongoDB access for accounts. Returns domain models, never documents;
never starts a transaction itself; turns driver errors into domain errors once, here."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from beanie import PydanticObjectId
from beanie.operators import Set
from bson.errors import InvalidId
from pymongo import AsyncMongoClient
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.errors import DuplicateKeyError

from app.accounts.domain import Account
from app.accounts.errors import AccountNotFoundError, DuplicateAccountError
from app.accounts.models import AccountDocument


def _to_domain(doc: AccountDocument) -> Account:
    return Account(
        id=str(doc.id),
        owner_email=doc.owner_email,
        kyc_reference=doc.kyc_reference,
        balance_cents=doc.balance_cents,
    )


def _object_id(account_id: str) -> PydanticObjectId:
    try:
        return PydanticObjectId(account_id)
    except InvalidId as exc:  # a malformed id names no account
        raise AccountNotFoundError(account_id) from exc


class BeanieAccountRepository:
    def __init__(self, uow: "MongoUnitOfWork") -> None:
        self._uow = uow

    @property
    def _session(self) -> AsyncClientSession | None:
        # every call passes it: a call without session= escapes the transaction
        return self._uow.session

    async def get(self, account_id: str, *, for_update: bool = False) -> Account:
        # for_update is not needed: inside a transaction MongoDB reports a
        # concurrent write to the same document as WriteConflict at write time.
        doc = await AccountDocument.get(_object_id(account_id), session=self._session)
        if doc is None:
            raise AccountNotFoundError(account_id)
        return _to_domain(doc)

    async def add(self, owner_email: str, kyc_reference: str) -> Account:
        doc = AccountDocument(owner_email=owner_email, kyc_reference=kyc_reference)
        try:
            await doc.insert(session=self._session)
        except DuplicateKeyError as exc:
            raise DuplicateAccountError(owner_email) from exc
        return _to_domain(doc)

    async def set_balance(self, account_id: str, balance_cents: int) -> None:
        result = await AccountDocument.find_one(
            AccountDocument.id == _object_id(account_id), session=self._session
        ).update(
            Set({AccountDocument.balance_cents: balance_cents}), session=self._session
        )
        if result.matched_count == 0:
            raise AccountNotFoundError(account_id)


class MongoUnitOfWork:
    """One client session and its transaction; the service says where it
    starts and ends. Needs a replica set: a standalone refuses transactions."""

    def __init__(self, client: AsyncMongoClient) -> None:
        self._client = client
        self.session: AsyncClientSession | None = None
        self.accounts = BeanieAccountRepository(self)

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        async with self._client.start_session() as session:
            # commits on exit, aborts on an exception
            async with await session.start_transaction():
                self.session = session
                try:
                    yield
                finally:
                    self.session = None
