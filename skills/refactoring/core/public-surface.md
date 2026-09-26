# The public surface and shims

**Verdict you produce:** who can rely on the names the step changes,
and for each one: callers changed, or a shim kept.

```
name:     <old dotted name> -> <new dotted name>
callers:  <all in this repository, found by core/every-reference.md | outside: <entry point | README | published package | stored data | not searched>>
shim:     <none: every caller changed | re-export in <file> | alias in <file>>
limits:   <what the shim does not keep: patches of the old name, overrides, stored paths>
verdict surface: <callers changed | shim kept | stop: contract>
```

## What others can rely on

Anything code outside the change can import, call, pass or store:

- every name without a leading underscore in an importable module,
  **whether or not it is in `__all__`**: in the lab `CENT` was left out
  of `__all__`, the split dropped it, and tests, ruff and mypy were all
  green while `from app.reports import CENT` failed
  (`tools/public_names.py` caught it);
- the module path itself (`app.helpers`), for imports, `python -m`,
  patch targets and dotted paths in config;
- parameter names, their order, their defaults, and the exceptions
  raised;
- `[project.scripts]` and `[project.entry-points]` in `pyproject.toml`;
- class paths recorded in stored data: a pickle names the class by its
  module (`app.reports.orders.Order` after a move), queues and caches do
  the same;
- names on the wire or in a database: those are contracts
  (`core/before-you-start.md`), not structure.

## Shim or change every caller

Change every caller, with no shim, only when all of these hold: every
caller is in this repository and was found (`core/every-reference.md`);
no entry point, script, config file or stored data outside the
repository names it; the package is not installed by other projects
(README, a published version, other teams). Otherwise, or when unsure,
keep a shim, and change the callers in this repository to the new name
anyway. A `DeprecationWarning` in the shim only if the person asks.

## Shims that worked in the lab

| Change | Shim at the old place | Lab |
| --- | --- | --- |
| function moved to another module | `from app.dates import parse_date as parse_date` | ruff and `mypy --strict` clean. A plain `from app.dates import parse_date` was `F401 [*]`, which `ruff check --fix` removes, and `mypy --strict` said `Module "app.helpers" does not explicitly export attribute "parse_date"` |
| module split into a package | `__init__.py` imports every public name from the submodules | `from app.reports.money import CENT as CENT, CURRENCY_SYMBOLS, format_money`; names in `__all__` need no `as` |
| function renamed | `get_user = fetch_user` after the new definition, and the old name kept in `__all__` | imports and calls of the old name work |
| class moved | a re-export, as for a function | an old pickle loaded through the re-export; without it: `AttributeError: Can't get attribute 'Order' on <module 'app.reports' ...>` |

## What a shim does not keep

- **Patches of the old name.** With `get_user = fetch_user`, a test
  that patches `app.users.get_user` replaces only the alias; code that
  calls `fetch_user` is not patched (lab: `assert 'unknown' == 'Mock'`).
  After a move, a patch of the old module misses code that now lives in
  the new one. Tests in this repository are changed in the step; other
  teams' tests go under *Not checked*.
- **Overrides of a renamed method.** With `get_user = fetch_user` in a
  class, a subclass that overrides `get_user` is no longer called by
  code that calls `self.fetch_user` (lab: the base's result came back,
  not the subclass's). A renamed method that subclasses may override is
  a change of the surface; say so and ask.
- **Stored class paths going forward.** Old pickles load through the
  re-export, but new ones record the new module, which older code
  cannot load; a rollback after new data is written breaks.
- **Seniority's change check.** Some correct shims are still reported
  as removals (`reference/change-check.md`).

## Never

- Never remove a shim in the same task that created it, unless asked;
  removing it later is a **Remove** task (`core/dead-code.md`).
- Never rename a public parameter as a refactoring: a caller passing it
  by keyword breaks (`TypeError: find() got an unexpected keyword
  argument 'exact'`).
- Never write a re-export as a plain import in a module that is not an
  `__init__.py`.
