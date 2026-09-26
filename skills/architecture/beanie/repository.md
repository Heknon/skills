# A repository over Beanie

**Verdict you produce:** the repository class, what each method returns
and raises, and its tests against a server.

Beanie 2.2.0 on PyMongo 4.18.2, MongoDB 8.0.32 as a single-node replica
set, *lab*. What each Beanie call sends to the server, and the query
patterns worth copying (projections, `$in` instead of `fetch_links`, a
dotted `$set` on the revision), are the mongodb skill's:
`skills/mongodb/beanie/` and `skills/mongodb/recipes/beanie_app/app/queries.py`.
This file is the class around them. The recipe:
`recipes/beanie_service/app/accounts/repository.py`.

## The contract

| Does | Never |
| --- | --- |
| holds every query for its documents; passes `session=` on every call | lets a route call `Document.find(...)` (L1) |
| returns domain models (`_to_domain(doc)`), ids as `str` | returns the `Document`, a raw dict, an aggregation's rows with `_id`, or `get_pymongo_collection()` (L6); returning the `Document` is a card exception where the codebase uses it as its domain model (decision AR3) |
| catches `DuplicateKeyError` at the write and raises a domain error `from exc` | lets it reach the route, or raises `HTTPException` (L8) |
| turns a malformed id into the not-found error | lets `bson.errors.InvalidId` escape as a 500 |
| checks `matched_count` of an update to detect a missing document | assumes the update found one |

## Calls it relies on (*lab*)

| Call | Result |
| --- | --- |
| `await Doc.get(PydanticObjectId())` for a missing id | `None` |
| `await Doc.get("nope")` | a pydantic `ValidationError`, so convert ids first |
| `PydanticObjectId("nope")` | `bson.errors.InvalidId: 'nope' is not a valid ObjectId, it must be a 12-byte input or a 24-character hex string` |
| `await Doc.find_one(Doc.id == oid).update(Set({...}))` | an `UpdateResult`; `matched_count` 1, or 0 for a missing document |
| `find_one(..., session=s).update(..., session=None)` | the update used `s`: Beanie keeps the find's session when the update's is `None` (`beanie/odm/interfaces/session.py`, `set_session`); removing both lost the rollback |
| `doc.insert(session=s)` of a duplicate unique key | `pymongo.errors.DuplicateKeyError` (`errors.md`) |

## The shape

```python
class BeanieAccountRepository:
    def __init__(self, uow: "MongoUnitOfWork") -> None:
        self._uow = uow

    @property
    def _session(self) -> AsyncClientSession | None:
        # every call passes it: a call without session= escapes the transaction
        return self._uow.session

    async def add(self, owner_email: str, kyc_reference: str) -> Account:
        doc = AccountDocument(owner_email=owner_email, kyc_reference=kyc_reference)
        try:
            await doc.insert(session=self._session)
        except DuplicateKeyError as exc:
            raise DuplicateAccountError(owner_email) from exc
        return _to_domain(doc)
```

The session comes from the unit of work (`sessions.md`); outside a
transaction it is `None` and each call is a plain write.

## Tests

`recipes/beanie_service/tests/test_repository.py`, skipped without
`MONGODB_URI`: domain models out; a duplicate owner is
`DuplicateAccountError` caused by `DuplicateKeyError`; a malformed id is
not found; a failed second write in one transaction is undone; a write
without `session=` is not undone; the wiring end to end. *lab:* 15
passed with the replica set; 9 passed and 6 skipped without it.
