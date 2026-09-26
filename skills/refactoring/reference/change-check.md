# Seniority's change check on a refactoring

Some setups run seniority's harness around the model
(`harness/seniority-checks/check_change.py`): it compares each changed
file with a snapshot taken before the first edit and sends failures
back. You never run it yourself. When it reports on a refactoring, this
page says which reports are real and which come from a shape it cannot
read, and what to write in the answer.

Measured on the harness after its second widening (it now follows
aliases, method aliases, `mod.name` and star-import shims, looks under
every `src` folder up to three levels down, and gives a function moved
into an existing file its old error-handler count), on the part-1 lab
cases, a matrix of shim shapes, and every step of the eleven recipes.
A third widening (its fixture is
`harness/seniority-checks/fixtures/move3/`) treats a public
module-level value as part of the API and lets a star shim re-export
only what the target's `__all__` lists; the last two rows of the next
table were rerun on it, with every recipe.

## What it reads correctly

| Shape | Result in the lab |
| --- | --- |
| function or class moved, old module re-exports it (`from pkg.core import parse`, with or without `as parse`, absolute or relative) | pass; a changed default in the new place is still reported: `parse default of 'strict' changed` |
| rename kept as an alias, `get_user = fetch_user` | pass; a changed default behind the alias is reported |
| method alias in a class, `open = unlock` | pass |
| attribute shim `parse = core.parse`, star shim `from pkg.core import *` (the name in the target's `__all__`, or no `__all__`) | pass |
| module split into a package (`util.py` to `util/__init__.py` re-exporting from submodules) | pass: `app/reports.py became the package app/reports/__init__.py` |
| `src` layout, and a package under `packages/<name>/src/` | pass, and a changed default is reported with absolute or relative re-exports |
| a function moved into a module that existed before, with its `except` that does not re-raise | pass: the handler keeps its old count (the `move-util` move) |
| a re-export from a module of the project that does not exist (`from pkg.cores import parse`) | fail: every name `removed or renamed`. Real: the import breaks |
| a provider or a method removed (recipes L3 `get_session`, L7 `Member.to_out`) | fail: `removed or renamed`. Real; name the removal and the search that found no caller |
| a public module constant or variable removed (recipe L2 `TIERS`, L9 `rates`) | fail: `app/main.py: TIERS was removed or renamed`. Real: an importer of `app.main.TIERS` breaks; re-export it, or name the removal and the search that found no importer. A private one (`_cache`) is not compared |
| a star shim whose target leaves the name out of `__all__` | fail: `save was removed or renamed`. Real: `from pkg.util import save` raises `ImportError: cannot import name 'save'`. List the names in the shim, or add the name to the target's `__all__` |

## What it reports although the refactoring is correct

| Shape | Report | Write in the answer |
| --- | --- | --- |
| a route's dependency parameter renamed or added (recipes L1, L3, L9) | `public-signature: get_user parameter 's' became 'users'; a caller passing it by name breaks`, or `convert gained required parameter 'rates'` | FastAPI fills that parameter; no caller passes it. The probe and the OpenAPI document are identical |
| an `except` narrowed from reading the message to catching a class (recipe L11) | `swallowed-errors: status_or_none has 1 new except block(s) that do not re-raise` | cite both handlers: the old one swallowed the same case and re-raised the rest |
| a rename asked for, with test calls renamed | `test-expectations: expectation removed or changed: 'assert parse("a") == "a"'` | the assert lines changed only the name called; the expected values are the same |
| a module moved or renamed with every caller changed and no shim | `files-deleted: pkg/util.py is in the snapshot but gone` | why no shim was needed (`core/public-surface.md`) |

A rename or signature change the person asked for is reported as
`public-signature` too; that is correct, and the answer names the ask.

## What it passes although something is wrong

| Shape | What it misses | What sees it |
| --- | --- | --- |
| a module `__getattr__` shim | treated as unreadable: pass, even when the name behind it changed its default (`(text, strict=True)` at run time) | `tools/public_names.py`, the probe |
| a function moved into a new file, gaining an `except` that does not re-raise | pass: files not in the snapshot are not compared | the diff, read before the commit |
| a commit moved out of a repository (recipe L5) | pass: it compares signatures, not what a body does | the test that failed first |
| anything else not in the snapshot: new files, and files never edited | not compared | the tests, import-all, the probe |

The tests, `tools/import_all.py`, `tools/public_names.py` and the probe
cover every row; run them as `core/checks.md` says, whatever the harness
reports.
