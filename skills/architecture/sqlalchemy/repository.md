# A repository over SQLAlchemy

**Verdict you produce:** the repository class, what each method returns
and raises, and its tests against a database.

The recipe: `recipes/sqlalchemy_service/app/accounts/repository.py`.

## The contract

| Does | Never |
| --- | --- |
| takes the request's `AsyncSession` in `__init__` | opens its own session or engine (L5) |
| runs every query for its table(s) | lets a route build a `select` (L1) |
| returns domain models, built from the row while the session is open (`_to_domain(row)`) | returns a row, `Row`, `Result`, `Select` or `dict` (L6) |
| `flush()`es after a write, so the INSERT or UPDATE runs now and its error surfaces here | `commit()` or `rollback()` (L5) |
| catches `IntegrityError` at that flush and raises a domain error `from exc` | lets the driver error leave, or raises `HTTPException` (L8) |
| raises the domain not-found error, or returns `None`, the way the codebase's other repositories do | mixes the two in one repository |

## The shape

```python
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
        row = AccountRow(owner_email=owner_email, kyc_reference=kyc_reference, balance_cents=0)
        self.session.add(row)
        try:
            await self.session.flush()
        except IntegrityError as exc:
            if _is_unique_violation(exc):
                raise DuplicateAccountError(owner_email) from exc
            raise
        return _to_domain(row)
```

`with_for_update()` compiled, *lab:* on the PostgreSQL dialect `... WHERE
accounts.id = %(id_1)s::INTEGER FOR UPDATE`; on SQLite the clause is
left out. Whether the lock holds under concurrent
requests was *not run on PostgreSQL*.

## Tests

`recipes/sqlalchemy_service/tests/test_repository.py`, against SQLite
by default and PostgreSQL when `DATABASE_URL` is set:

- add and get return `Account` domain models equal to each other;
- a duplicate owner raises `DuplicateAccountError` whose `__cause__` is
  `IntegrityError`;
- a failed second write inside one `transaction()` leaves the first
  undone;
- one end-to-end request with no override.

*lab:* 13 passed (SQLite); each of these mutants failed at least one
test: the translation removed, `kyc_reference` added to the response
schema, a `commit()` added to `set_balance`, the service's
`transaction()` removed.
