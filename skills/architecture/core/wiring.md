# Wiring and swapping

**Verdict you produce:** the provider chain from a request to the
service, the override a test uses, and the test run.

```
chain:    <route param> <- Depends(<provider>) <- Depends(<provider>) <- ...
file:     <where the providers live>
override: app.dependency_overrides[<provider>] = <replacement>, cleared in <fixture>
test:     <test and run line>
```

How `Depends` works (the per-request cache, `yield` teardown and its
scope, how overrides are looked up, clearing them) is the api skill's:
`skills/api/fastapi/dependencies.md` and
`skills/api/fastapi/testing.md`. This
file is what to inject and what to swap.

## The chain

From the recipes (`recipes/sqlalchemy_service/app/`):

```
router.py      service: AccountServiceDep
dependencies.py  get_account_service(uow = Depends(get_unit_of_work))
dependencies.py  get_unit_of_work(session = Depends(get_session))
db.py            get_session(request) -> one AsyncSession per request
```

- One provider per object, each taking the one below it. The route names
  only the service.
- Providers live in the feature's `dependencies.py`; shared ones (the
  session, settings) in the package's `db.py` or `dependencies.py`, as
  the card says.
- Process-wide objects (the engine, the Mongo client) are created in
  the lifespan and read from `request.app.state` by a provider.
- A service or repository is never built at module level or inside the
  route (L9).

## Swapping in tests: which layer a test fakes

| Test of | Fakes | How |
| --- | --- | --- |
| the rules (service) | the unit of work or repository | construct the service with a fake: `AccountService(FakeUnitOfWork())`; no FastAPI, no database |
| the HTTP mapping (route) | the service's dependencies | `app.dependency_overrides[get_account_service] = lambda: AccountService(fake_uow)` |
| the repository and unit of work | nothing | a real database: SQLite by default, PostgreSQL or a Mongo replica set when reachable |
| the wiring itself | nothing | one end-to-end test with no override (`test_the_wiring_end_to_end` in both recipes) |

The fake keeps the real contract: domain models in, domain errors out,
and a `transaction()` that restores its data when the block raises, so
service tests see rollback (`recipes/*/tests/conftest.py`). A fake that
cannot fail proves little: the recipes' fake can be told to fail a
write (`broken`), which is how the service test of a rollback can fail.

## The override key

The key is the provider the route's `Depends(...)` names. *lab,* sandbox
wrong-override: the route used `Depends(get_repo)` and the test set
`app.dependency_overrides[NoteRepository]`: the real repository ran,
`test_read_note` failed with 404, and `test_missing_note_is_404`
passed only because the real folder was empty. Keying by `get_repo`
fixed the first and made the second able to fail. Changing the route to
`Depends(NoteRepository)` to suit the test is the wrong fix.

## A lifespan that connects

Overrides do not replace the lifespan. *lab,* the Beanie recipe: the
lifespan calls `init_beanie`, which needs a server, so route tests with
a fake service would need MongoDB anyway. The recipe's app factory takes
`connect=False` for those tests (`recipes/beanie_service/app/main.py`).
A SQLAlchemy lifespan that only creates the engine does not connect:
*lab,* the SQL recipe's route tests ran with no database file created.

## Never

- Never patch a module global to swap a dependency (`monkeypatch.setattr
  (routes, "repo", fake)`): make it a provider and override that.
- Never leave an override set: clear it in the fixture that set it.
