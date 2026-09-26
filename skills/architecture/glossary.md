# Glossary

One sentence per term. Use these words and no synonyms.

| Term | Meaning |
| --- | --- |
| layer | A group of modules with one job (routing, rules, data access, storage) that imports only layers below it. |
| edge | The outermost layer that talks to the outside: HTTP routes, a CLI, a worker's entry point. |
| router | The module of path operations (`APIRouter` or `app` routes); parses requests, calls one function below, maps the result to a response. |
| path operation | One decorated route function, such as `@router.get("/orders/{id}")`. |
| service | The module or class holding the rules of a use case; called by routes, workers and CLIs alike; knows no HTTP. |
| repository | A class or module that holds all queries for one kind of stored thing and returns domain models; also called a DAL or `crud.py`. |
| DAL | Data access layer: the codebase's own name for the repositories, sometimes one module of functions. |
| crud module | A per-feature module of query functions (`crud.py`) used directly by routes, with no service layer. |
| domain model | The object the service works with: a pydantic model or dataclass with no HTTP and no database behaviour. |
| schema | A request or response model: the HTTP contract (`UserIn`, `UserOut`). |
| database model | The class the ORM or ODM stores: a SQLAlchemy mapped class (row) or a Beanie `Document`. |
| mapping | The code that builds one model from another (`AccountOut.from_domain`, `_to_domain(row)`). |
| provider | A function named in `Depends(...)` that builds a session, repository or service for a request. |
| wiring | The chain of providers from a request to a service. |
| override | An entry in `app.dependency_overrides` that replaces a provider, keyed by the provider function. |
| fake | A test double that keeps the real contract in memory, such as a dict-backed repository. |
| unit of work | The object that holds one session and its repositories and starts and ends one transaction (`uow.transaction()`). |
| transaction owner | The one layer that decides where a transaction begins and commits: the service, in this skill. |
| flush | Sending pending SQL to the database inside the open transaction, without committing. |
| driver error | An exception from the database library: `DuplicateKeyError`, `IntegrityError`. |
| domain error | An exception the application defines for a failure its callers handle by type. |
| error category | A domain error class the HTTP edge maps to one status: `NotFoundError` 404, `ConflictError` 409. |
| translation | Catching an error of one layer and raising the next layer's error `from` it, once per boundary. |
| structure card | The short record of how a codebase is built, made before any change (`core/card.md`). |
| layout | How modules are grouped: by layer, by feature, crud per feature, hexagonal. |
| precedent | An existing definition of the same kind, at the same level, that shows where a new one goes. |
| kind | What a new thing is for placement: exception, constant, enum, type alias or Protocol, helper, settings field, schema, provider. |
| grab bag | A module named for nothing in particular (`utils.py`, `helpers.py`, `common.py`) that collects unrelated helpers. |
| setting | A value that differs by environment, read by pydantic-settings; not a constant. |
| violation | A line that breaks a layering rule, named by a checklist ID L1 to L11. |
| shape | The before and after of one violation, with a test both pass (`shapes/`). |
| card exception | Something the checklist would flag that the codebase's structure allows, so it is not a finding. |
