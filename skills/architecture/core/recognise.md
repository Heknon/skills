# Recognise the structure

**Verdict you produce:** a structure card (`core/card.md`), filled in
from files you read, before any change.

The card is what lets you follow the codebase instead of a textbook.
Making it takes a few searches and reads; skipping it is how a
`services/` folder lands in a project that uses `crud.py`.

## Steps

1. **Find the app and its routes.** Search with the editor's `grep`
   and a `**/*.py` filter. Patterns are in code blocks because they
   contain `|`, which a table cannot show safely:

   ```
   the FastAPI app          ^\s*\w+\s*=\s*FastAPI\(
   an app factory           ^\s*def\s+create_app\(
   routers included         include_router\(
   route decorators         ^\s*@\w+\.(get|post|put|patch|delete|api_route)\(
   other entry points       ^if __name__ == .__main__.:
   ```

   Also read `[project.scripts]` in `pyproject.toml`. How the program starts and which entry points exist is navigation's
   Orient question (`skills/navigation/core/orient.md`,
   `python/entry-points.md`). A worker or CLI that calls the same code
   as a route matters to every later decision: note it.
2. **Trace one request from route to database.** Pick a route that
   writes. Follow each call to its definition (navigation's Follow,
   `core/follow.md`) and write each hop as `path:line`: route, the
   function it calls, the one that calls, down to the ORM or ODM call.
   Note every `Depends(...)` on the way: those are the providers.
3. **Name the layout** from the tree and the trace, with
   `core/layouts.md`: by layer, by feature, crud per feature, hexagonal,
   or flat (no layers).
4. **Find where each concern lives.** One search each; write the path of
   the file that holds it, or `none`:

   ```
   database models      ^class\s+\w+\((Document|Base|DeclarativeBase|SQLModel)\b
   request/response     ^class\s+\w+\(BaseModel\)   (in route files and schemas*)
   mapping              from_attributes|model_validate\(|from_\w+\(|to_\w+\(
   providers            Depends\(\s*\w+             (then locate each name)
   commits, sessions    \.commit\(\)|\.begin\(\)|start_session\(|start_transaction\(
   error classes        ^\s*class\s+\w+\(\s*[\w.]*(Error|Exception)\b
   error handlers       exception_handler\(|add_exception_handler\(
   settings             BaseSettings
   ```

   Domain models are the classes the service returns that are neither
   database models nor schemas; there may be none (the database model
   serves as the domain model).

5. **Record the precedent per kind** for anything the task will add
   (`placement/place-a-thing.md`, step 2): where exceptions, constants,
   enums, helpers and providers live, and how their files are named.
6. **Read two siblings of what you will add.** If you will add a route,
   read two routes of the same feature; a repository method, two
   methods. Their shape (return types, how a missing row is reported,
   how errors leave) is the precedent for yours.
7. **Write the card** (`core/card.md`). Mark anything you inferred
   rather than read.

## When the codebase is uneven

Two features built two ways is common. Follow the feature you are
changing. For a new feature, follow the most recent one (`git log
--diff-filter=A --format=%ad -- <folder>` shows when each folder was
added; navigation's History). Say which one you followed and why.

## Never

- Never decide the layout from folder names alone: a `services/` folder
  of forwarding functions is not a service layer, and a `models.py` may
  hold schemas. The trace decides.
- Never start the change before the card exists.
- Never "fix" the structure while recognising it. Deviations go in the
  card; changing them is a separate, asked-for task.
