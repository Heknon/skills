# Worked example: a crud-per-feature codebase, and one more endpoint

Kinds: Recognise, Place. Copy the order of the steps and the answer's
shape. The outputs are from a lab run (sandbox crud-by-feature, FastAPI
0.141.1, pytest 9.1.1).

## The ask

> Add an endpoint to archive a project. Archived projects must no
> longer appear in GET /projects.

## Steps

1. **Routes and the app** (`core/recognise.md` step 1). `grep`
   `include_router\(` found `app/main.py:17` (users) and `:18`
   (projects). Route decorators: `app/projects/router.py:14, 21, 26`
   and the users router.
2. **Trace a write** (step 2): `app/projects/router.py:15`
   `create_project` -> `app/projects/crud.py:6` `create_project(db,
   name, owner_id)` -> `db.projects[row.id] = row` in the in-memory
   `Database` (`app/db.py`). The provider is `get_db` in `app/db.py`,
   reading `request.app.state.db`.
3. **Layout** (`core/layouts.md`): crud per feature. Each feature has
   `router.py`, `crud.py`, `schemas.py`; routes call crud functions
   directly; there is no service module anywhere
   (`find_path` `**/service*.py`: none).
4. **Two siblings** (step 6): `get_project` returns `None` for a
   missing row and the route raises `HTTPException(404, f"project
   {project_id} not found")` (`router.py:30`); `list_projects` sorts by
   id (`crud.py:16`).
5. **The card**:

   ```
   layout:       crud per feature: app/users/, app/projects/ (router, crud, schemas)
   entry points: app/main.py:16 app = FastAPI(lifespan=lifespan)
   trace:        app/projects/router.py:15 create_project -> app/projects/crud.py:6
                 create_project -> Database.projects (app/db.py)
   layers:       router, crud; no service layer
   models:       rows are dataclasses in app/db.py; schemas per feature
                 (from_attributes); no separate domain model
   mapping:      ProjectOut.model_validate(row) in the router
   wiring:       get_db (app/db.py) from app.state
   transactions: none (in memory)
   errors:       HTTPException in routers; no custom errors
   precedent:    a query -> the feature's crud.py; a route -> its router.py
   ```

6. **Place** (`core/place.md`): a crud function, a route, a field. No
   `services/` folder and no `ProjectService`: the card has no service
   layer, and one route does not earn one (invariant 3).
   - `app/db.py`: `archived: bool = False` on `ProjectRow`;
   - `app/projects/crud.py`: `archive_project(db, project_id) ->
     ProjectRow | None`, and `list_projects` filters `not p.archived`
     (the filter is a query, so it lives in crud, not in the route);
   - `app/projects/schemas.py`: `archived: bool` on `ProjectOut`
     (an added response field: additive, the api skill's
     `core/compatibility.md`);
   - `app/projects/router.py`: `POST /projects/{project_id}/archive`,
     404 like its siblings.
7. **Tests** in `tests/test_projects.py`, in the file's style: archive
   then list, and archive of a missing project.
8. **Run**: `uv run pytest -q` -> `6 passed in 0.36s`. Broke the filter
   (`if True` instead of `if not p.archived`): the list test failed;
   restored.

## The answer

```
## Structure
layout: crud per feature (app/projects/{router,crud,schemas}.py), no
service layer; trace app/projects/router.py:15 -> app/projects/crud.py:6
-> Database (app/db.py); 404s are HTTPException in the router
(app/projects/router.py:30); rows are dataclasses in app/db.py.

## Result
- app/db.py: ProjectRow.archived (default False).
- app/projects/crud.py: archive_project(); list_projects() skips archived
  rows (queries live in crud.py).
- app/projects/schemas.py: ProjectOut.archived (additive field).
- app/projects/router.py: POST /projects/{project_id}/archive, 404 for a
  missing project, as the other routes do.
- tests/test_projects.py: two tests.
No service layer added: the codebase has none.

## Checked
- uv run pytest -q: 6 passed in 0.36s.
- With the list filter broken, test_archive_hides_from_list failed;
  restored.

## Not checked
- Clients that compare ProjectOut exactly would see the new field.
```
