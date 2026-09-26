# Seniority's change check on a refactoring

Some setups run seniority's harness around the model
(`harness/seniority-checks/check_change.py`): it compares each changed
file with a snapshot taken before the first edit and sends failures
back. You never run it yourself. When it reports on a refactoring, this
page says which reports are real and which come from a shape it cannot
read, and what to write in the answer.

Measured on the harness as of the roadmap's R7 change (it follows a
`from x import name` re-export to the defining module, and compares a
module that became a package with its `__init__.py`).

## What it reads correctly

| Shape | Result in the lab |
| --- | --- |
| function moved, old module re-exports it: `from pkg.core import parse` or `from pkg.core import parse as parse` | pass; a changed default in the new place is still reported: `parse default of 'strict' changed` |
| class moved and re-exported | pass; its methods are compared where the class now lives |
| module split into a package (`util.py` to `util/__init__.py` re-exporting from submodules, absolute or relative imports) | pass: `app/reports.py became the package app/reports/__init__.py` |
| a `src` layout, absolute re-export | pass, and a changed default is reported |

## What it reports although the refactoring is correct

| Shape | Report | Write in the answer |
| --- | --- | --- |
| a rename kept as an alias, `get_user = fetch_user` | `public-signature: get_user was removed or renamed` | the alias line, and a probe or import through the old name |
| a method alias in a class, `open = unlock` | `Box.open was removed or renamed` | as above |
| a star re-export, `from pkg.core import *` | every name `removed or renamed` | prefer explicit re-exports (`steps/move-module.md`) |
| an attribute shim, `parse = core.parse`, or a module `__getattr__` | every name `removed or renamed` | prefer explicit re-exports |
| a function moved into a module that existed before, and its body has an `except` that does not re-raise | `swallowed-errors: dates.py: parse_date has 1 new except block(s)` | the handler was moved, not added: cite the old line |
| a rename asked for, with test calls renamed | `test-expectations: expectation removed or changed: 'assert get_user(1)["name"] == "Ada"'` | the assert lines changed only the name called; the expected values are the same |
| a module moved or renamed with every caller changed and no shim | `files-deleted: pkg/util.py is in the snapshot but gone` | why no shim was needed (`core/public-surface.md`) |

A rename or signature change the person asked for is reported as
`public-signature` too; that is correct, and the answer names the ask.

## What it passes although something is wrong

| Shape | What it misses |
| --- | --- |
| a re-export from a module that does not exist (`from pkg.cores import parse`, a typo) | passes: an import it cannot resolve is treated as outside the working directory. import-all fails it |
| an absolute re-export in a package that is not at the root or in `src/` (for example `packages/lib/src/pkg`) | passes even with a changed default; a relative re-export there is compared |
| anything not in the snapshot: new files, and files never edited | not compared |

The tests, `tools/import_all.py` and `tools/public_names.py` cover all
three; run them as `core/checks.md` says, whatever the harness reports.
