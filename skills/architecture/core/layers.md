# What each layer may and must not do

**Verdict you produce:** for a piece of code, the layer it belongs in,
with the rule that decides it.

Layers are named by job, whatever the codebase calls its files. A
codebase without some layer (no service in a crud-per-feature app) does
not get one from you; the jobs of the missing layer stay where the card
says they are.

| Layer | Does | Must not | Checklist |
| --- | --- | --- | --- |
| **router** (path operations) | parse and validate the request with schemas; call one service or repository function; map the result to a response schema; set status and headers | query the database; hold rules; commit; catch driver errors; return a database model | L1, L2, L3, L5, L8 |
| **dependencies** (providers) | build sessions, repositories, services for one request; read settings | hold rules or queries | L9 |
| **service** | the rules of a use case; call repositories; own the transaction through a unit of work; raise domain errors | import `fastapi` or `starlette`; raise `HTTPException`; take a `Request`; return a response or status | L4, L5 |
| **repository** (DAL, crud) | every query for its kind of thing; map rows or documents to domain models; translate driver errors, once; flush | commit or open its own session; return rows, dicts, cursors or `Select`s; raise `HTTPException`; import schemas or services | L5, L6, L7, L8 |
| **database models** | the table or collection: columns, indexes, relationships | appear in a route signature or response; import schemas or services | L3, L7 |
| **domain models** | the data the service works with; small methods about their own state | import anything above them; do IO | L7 |
| **schemas** | the HTTP contract: request and response bodies; mapping from domain models | hold rules; be the database model | L3 |
| **errors** | the base, categories, feature errors | import anything but the base | L11 |

## Import direction

```
router -> schemas, dependencies -> service -> repository -> database models -> domain -> errors
```

Each module imports only modules to its right. Schemas may import domain
models (to map from them); services and repositories do not import
schemas in new code. A codebase whose services accept schemas is a card
exception: follow it for the feature you change, and say so.

The lab's recipes hold this with an import-linter contract, for a
project that already uses the tool (`recipes/README.md`); the order
inside the `layers` list matters: *lab,* import-linter 2.15, with
`schemas` listed below `repository` a repository importing a schema
passed; with `"schemas | dependencies"` as the second layer it was
reported: `app.accounts.repository is not allowed to import
app.accounts.schemas`.

## Deciding where a piece of code goes

1. Does it talk HTTP (status, headers, request objects)? Router.
2. Does it decide something about the domain (a limit, a price, a state
   change) that a worker would also need? Service, or the domain model
   if it is about one object's own state.
3. Does it read or write storage? Repository.
4. Does it turn one model into another? The mapping sits on the side
   that knows both: rows to domain in the repository, domain to schema
   in the schema (`from_domain`) or the router (`core/boundary-models.md`).
5. Does it build an object for a request? A provider (`core/wiring.md`).

If the card's layer for that job is missing, put the code where the card
says that job is done today, and mention the smell only if it matters
to the task.
