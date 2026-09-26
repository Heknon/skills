# Beanie and PyMongo errors, translated

*lab,* Beanie 2.2.0, PyMongo 4.18.2, MongoDB 8.0.32.

| Case | Raised | Translate to |
| --- | --- | --- |
| `insert()` with a duplicate unique key | `pymongo.errors.DuplicateKeyError`; MRO `DuplicateKeyError`, `WriteError`, `OperationFailure`, `PyMongoError`; `code` 11000; `details` keys `index`, `code`, `errmsg`, `keyPattern`, `keyValue`; message `E11000 duplicate key error collection: archprobe.users index: email_1 dup key: { email: "a@x" }` | a `ConflictError` subclass (`DuplicateAccountError`) |
| a malformed id given to `PydanticObjectId(...)` | `bson.errors.InvalidId` | the not-found error |
| a document built before `init_beanie` | `beanie.exceptions.CollectionWasNotInitialized` (empty message) | none: a startup or test-setup bug |
| a stale write with `use_revision` | `RevisionIdWasChanged` (the mongodb skill's `beanie/writes.md`) | a `ConflictError` subclass, or a retry |
| a write conflict inside a transaction | `WriteConflict`, labelled `TransientTransactionError` (mongodb's `core/transactions.md`) | a retry of the whole use case, or a `ConflictError` |

`keyPattern` tells which unique index failed when a collection has
several: check it before choosing the domain error, and re-raise
anything unexpected unchanged.

```python
try:
    await doc.insert(session=self._session)
except DuplicateKeyError as exc:
    if "owner_email" not in (exc.details or {}).get("keyPattern", {}):
        raise
    raise DuplicateAccountError(owner_email) from exc
```

*lab:* for a unique index on `owner_email`, `exc.details["keyPattern"]`
was `{'owner_email': 1}`. (The recipe has one unique index, so it
translates every `DuplicateKeyError`.)

The error message holds the duplicate value (`dup key: { email:
"a@x" }`): it is personal data in a log line. The domain error's
`__str__` leaves it out; the `from exc` cause keeps it for the server
log only (`placement/custom-errors.md`).
