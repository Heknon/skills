# Rename

Give a function, class, method, variable, constant or module-level name
a new name. Renaming a module file is `move-module.md`; renaming a
parameter is `change-signature.md`.

## Preconditions

- The name is not a contract (`core/before-you-start.md` step 1): not a
  JSON field, route, stored field, option or environment variable.
- The new name does not exist yet in the module or its imports
  (`git grep -n -w -I <new>` finds nothing that would clash).
- Public: decide the shim first (`core/public-surface.md`).

## Mechanics

1. List every reference (`core/every-reference.md`), all files. Mark each
   hit edit or leave.
2. Rename the definition.
3. If public and a shim is needed, add the alias right after the new
   definition and keep the old name in `__all__`:

   ```python
   def fetch_user(user_id: int) -> dict[str, object] | None:
       ...


   get_user = fetch_user  # old name, kept for callers outside this repository
   ```

4. Edit every `edit` hit: calls, imports, `__all__`, patch targets,
   strings, config, packaging, docs.
5. Search again: only `leave` hits remain.
6. Checks (`core/checks.md`) with `import_all.py --config` on each config
   file that had a hit; the probe calls each dynamic hit.
7. Commit: "Rename get_user to fetch_user".

## Traps seen in the lab

| Missed hit | What happened |
| --- | --- |
| `__all__` | only ruff saw it: `F822 Undefined name 'get_user' in '__all__'`; mypy 2.3.1 said `Success`; `from app.users import *` would fail |
| `mock.patch("app.users.get_user", ...)` | the test failed: `AttributeError: <module 'app.users' ...> does not have the attribute 'get_user'` |
| `getattr(source, "get_user", None)` with a fallback | silent: `resolve(1)` returned `{'id': 1, 'name': 'unknown'}`; all 6 tests passed |
| `call: app.users.get_user` in `config/jobs.yaml` | silent until the job runs: `AttributeError: module 'app.users' has no attribute 'get_user'`; `import_all.py --config config/jobs.yaml` reported it |
| a docs page | silent |
| `AdminClient.get_user`, another class's method | a replace-all would have renamed it too; it is a different thing and stays |

With the alias kept, a test patching `app.users.get_user` patched only
the alias, and `display_name` (which now calls `fetch_user`) returned
the real value: `assert 'unknown' == 'Mock'`. Change such patch targets
in this repository in the same step.

## Methods

A method is called as `obj.name(...)` on objects whose type search
cannot see. Search `\.name\b` and `def name\b` in every class: a
subclass that overrides the old name is not called any more after the
rename, even with an alias in the base (`core/public-surface.md`).
mypy does not check calls inside functions without annotations, and no
checker sees `obj.old()` on an untyped parameter (`core/checks.md`).

## Probe inputs

Every dynamic hit: the call that goes through `getattr`, the table, or
the config file, with an input that reaches it.

**Done when:** the final search shows only explained hits, and the
checks and the probe are green.
