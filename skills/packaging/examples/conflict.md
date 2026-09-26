# Worked example: a resolver conflict in a dependency group

Kinds: Dependencies, Metadata. Copy the order of the steps and the
answer's shape. Outputs are from a lab run on uv 0.12.19; the public
index stood in for the mirror so the resolver saw every released version.

## The ask

> I added pytest-asyncio to the dev group and now `uv lock` fails. Get it
> working, just remove whatever pins are in the way.

## Steps

1. **Run it and copy the whole error** (`core/dependencies.md`):
   ```
   error: No solution found when resolving dependencies
     cause: Because pytest-asyncio>=1.0.0,<=1.2.0 depends on pytest>=8.2,<9 and pytest-asyncio>=1.3.0,<=1.4.0a0 depends on pytest>=8.2, we can conclude that pytest-asyncio>=1.0.0,<=1.4.0a0 depends on pytest>=8.2.
            And because pytest-asyncio>=1.4.0a1 depends on pytest>=8.4 and digest:dev depends on pytest<8, we can conclude that digest:dev and pytest-asyncio>=1.0.0 are incompatible.
            And because digest:dev depends on pytest-asyncio>=1.0 and your project requires digest:dev, we can conclude that your project's requirements are unsatisfiable.
   ```
2. **Name the two sides.** Every pytest-asyncio 1.x needs pytest 8.2 or
   later; the `dev` group (`digest:dev`) says `pytest<8`. The runtime
   dependencies are not involved.
3. **Find why each bound is there.** `pytest-asyncio>=1.0` is what was
   just asked for. The pin has a comment:
   ```toml
   # pytest 8 broke our fixture plugin (acme-fixtures < 2.1); see ops#88.
   "pytest<8",
   ```
   Is acme-fixtures still used? `git grep acme-fixtures` finds only that
   comment: no dependency, no import. The pin's reason is gone.
4. **Change that one requirement.** The person asked to remove "whatever
   pins are in the way"; only one is, so only one changes, and the
   httpx bound stays. `pytest<8` becomes `pytest>=8.4` (the floor the
   newest pytest-asyncio needs), comment removed with its reason.
5. **Lock and look:**
   ```
   uv lock                                   # Resolved 15 packages
   uv tree --invert --package pytest
   ```
   ```
   pytest v9.1.1
   ├── pytest-asyncio v1.4.0
   │   └── digest v0.3.0 (group: dev)
   └── digest v0.3.0 (group: dev)
   ```
6. **Run the tests:** `uv run pytest` with one async test: `1 passed`.

## The answer

```
## Result
The dev group pinned pytest<8, and every pytest-asyncio 1.x needs
pytest>=8.2. The pin was for acme-fixtures < 2.1 (ops#88), which the
project no longer uses (git grep finds only the comment). Replaced
"pytest<8" with "pytest>=8.4" in [dependency-groups] dev; nothing else
changed. uv.lock now has pytest 9.1.1 and pytest-asyncio 1.4.0.

## Checked
- uv lock before: "No solution found", digest:dev pytest<8 against
  pytest-asyncio's pytest>=8.2. After: "Resolved 15 packages".
- uv tree --invert --package pytest: pytest 9.1.1, needed by
  pytest-asyncio 1.4.0 and the dev group.
- uv run pytest: 1 passed.

## Not checked
- CI with the new pytest major version; the suite here has one test.

## Needs a person
- none
```
