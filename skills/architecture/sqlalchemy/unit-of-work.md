# The unit of work over SQLAlchemy

**Verdict you produce:** the unit of work class, and where the service
enters it.

```python
class SqlUnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.accounts = SqlAccountRepository(session)

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        async with self.session.begin():   # commit on exit, rollback on an exception
            yield
```

(`recipes/sqlalchemy_service/app/accounts/repository.py`.) It lives
beside the repositories it holds; a codebase with several features may
give it its own module.

## Rules (*lab*, SQLAlchemy 2.1.1)

- **Enter it before the first statement of the use case.** A read
  before `transaction()` autobegins, and `begin()` then fails with
  `A transaction is already begun on this Session.` So the service's
  method starts with `async with self.uow.transaction():` and reads
  inside it.
- **Every SQL use case enters it, reads too.** Without it a write is
  never committed: the recipe's mutant without `transaction()` in
  `open_account` lost the insert (`AccountNotFoundError: account 1 not
  found` on the next read).
- **One transaction per use case, not per request.** Two service calls
  in one request are two units; that is the service's decision.
- **The service sees a `Protocol`, not this class.** `UnitOfWork` and
  `AccountRepository` are Protocols in `service.py`, so the service
  imports no SQLAlchemy (the import-linter contract checks it) and a
  fake satisfies them in tests.

## A codebase that commits in a dependency

```python
async def get_session():
    async with sessionmaker() as session:
        yield session
        await session.commit()
```

Accepted where the card shows it (decision AR4), with
`Depends(get_session, scope="function")`: *lab,* an INSERT that failed
at that commit gave the client **201** with the default scope and 500
with `scope="function"`. Then no repository or route commits, and the
service has no `transaction()`: one request is one unit.
