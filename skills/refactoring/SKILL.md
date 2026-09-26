---
name: refactoring
description: Change the structure of Python code without changing what it does, in small named steps, each checked and committed before the next. Refactor, restructure, clean up, tidy, simplify, rename a function, class, method, parameter or module, move a function or module, split a long module into a package, extract or inline a function, variable or class, introduce a parameter object, replace a conditional or a magic number, delete dead or unused code, untangle a diff that mixes a refactoring with a behaviour change, and make untested legacy code safe to change with characterization tests, golden masters and seams. Reshape a FastAPI service towards the architecture skill's shapes, step by step: move logic out of a router into a service, a query into a repository, a database model off the HTTP boundary, HTTPException out of a service, commits into a unit of work, a module-level object behind a provider. Every rename and move is done by search and edit, without IDE refactoring tools, and proven complete by searches, the tests, the type checker and an import-everything check. Verified on Python 3.12 with pytest 9.1, ruff 0.16, mypy 2.3, pyright 1.1.414, git 2.43, and FastAPI 0.141 with SQLAlchemy 2.1 for the recipes.
---

# Refactoring

This skill knows how to change structure while keeping behaviour: pin
what the code does, take one step from the catalogue, prove every
reference was found, check, commit, and undo a step that goes red.
Every command, message and trap in it was run on Python 3.12.14, pytest
9.1.1, ruff 0.16.9, mypy 2.3.1, pyright 1.1.414 and git 2.43.0, and the
recipes on FastAPI 0.141.1, pydantic 2.13.5 and SQLAlchemy 2.1.1 on
aiosqlite. Nothing is written from memory: find it here, or run it.

Read this file, then load only what the task needs. Seniority is loaded
too; its behaviour probe (`core/scope.md` question 6) and its habits are
not repeated here.

## Read the versions first

```powershell
uv run --no-sync python -VV
uv tree --frozen --only-group dev --depth 1   # which checkers the project has
git --version
git status
```

A check that is not in the project cannot be run; say so under *Not
checked* rather than installing it. Which tool really runs, and how CI
runs it, is the linting skill's (`skills/linting/core/run-like-ci.md`).

## The kinds of task

| Kind | You were asked to | Load |
| --- | --- | --- |
| **Plan** | say how to restructure something, without doing it | `core/before-you-start.md`, `core/plan-steps.md`, the `steps/` file of each step |
| **Step** | do one named refactoring: rename, extract, inline, move, split, change a signature | `core/before-you-start.md`, `core/step-loop.md`, the `steps/` file; for a rename, move or signature change also `core/every-reference.md` and `core/public-surface.md` |
| **Reshape** | move code towards a target shape: a service out of a router, a repository, separate DB and API models, domain errors, a unit of work, a provider to override | `recipes/README.md`, then the recipe of the checklist ID (`recipes/L<n>-*.md`); the end state is the architecture skill's `shapes/L<n>-*.md`; each recipe step goes through `core/step-loop.md` |
| **Pin** | make untested code safe to change | `legacy/characterization.md`, `legacy/seams.md`, and `legacy/golden-master.md` for many outputs |
| **Tidy** | "clean up", "improve", "refactor" with no named result | `core/before-you-start.md`, `core/plan-steps.md`, then **Step** for each step |
| **Remove** | delete dead or unused code | `core/dead-code.md`, `core/every-reference.md` |
| **Untangle** | commit or split a change that mixes structure and behaviour | `core/untangle.md` |

After every step, `core/checks.md`. A bug found on the way:
`core/refactor-or-fix.md`, at once.

## Where the facts are

| Folder | Holds |
| --- | --- |
| `core/` | the procedures, each ending in a verdict |
| `steps/` | the catalogue: rename, change signature, extract function, inline function, extract variable, extract class, introduce parameter object, move function, move module, split module, replace conditional, replace magic value; each with preconditions, mechanics and the traps seen in the lab |
| `legacy/` | characterization tests, golden masters, seams (clock, files, environment), sprout and wrap |
| `recipes/` | one per layering violation L1 to L11 of the architecture skill: the steps from its shape's before to its after, each diff, commit and check, and the traps seen; `run_recipes.py` replays them |
| `tools/` | `import_all.py` (imports every module, resolves dotted paths in config, imports scripts) and `public_names.py` (public names and signatures, to compare before and after), with a page each |
| `reference/` | `change-check.md` (what seniority's harness reports on a correct refactoring, and what it misses), `windows.md` |
| `examples/` | a rename proven complete (`rename-everywhere.md`), a move with a shim (`move-with-shim.md`), a red step undone (`red-step-undone.md`), a function pinned before restructuring (`pinned-function.md`) |

`glossary.md` fixes the words. The tools run with `uv run --no-sync
python <skill>/tools/<name>.py` from the project's root folder.

## Invariants

1. **Pin before the first edit.** Tests that run the code, or a
   behaviour probe, exist and pass before any change. None: the task
   becomes **Pin** first.
2. **One step, one check, one commit.** A step is named from the
   catalogue. The checks in `core/checks.md` run after it, and a green
   step is committed before the next one starts.
3. **Red means undo.** A step that turns any check red is undone
   (`git stash push --include-untracked`), then redone smaller or
   differently. Never edit a test, a conftest or another file to make a
   red step green.
4. **No behaviour change in a refactoring commit.** A bug, an odd value
   or a better default found on the way is a finding: noted, pinned if
   needed, and fixed only in its own commit when asked
   (`core/refactor-or-fix.md`).
5. **A rename or move is done when every hit is edited or explained**
   and a check that fails on a miss has run: the search again, the
   tests, the type checker, `tools/import_all.py` with the config files.
6. **A moved or renamed public name keeps a shim** unless every caller
   is in this repository and none comes from outside (entry point,
   installed package, other service, stored data).
7. **Contract names are not structure.** A serialized field, a route, a
   stored field, a command-line option, an environment variable: renaming
   one changes behaviour for someone else. Stop and say so.
8. **Nothing is deleted on one search.** `core/dead-code.md` first.
9. **Search and edit only.** No IDE refactoring; `ruff check --fix`
   only for imports, and never on a file whose unused import is a shim.
10. **Commits stay local.** Never push; that is the person's call.

## What you say when you finish

End with these headings, each with `none` when empty. If other skills
are loaded, their headings come after these, seniority's last.

```
## Steps
<each step: its catalogue name, the commit (hash and subject), and the
checks run after it with their summary lines>

## References
<for a rename, move or removal: every hit, edited or explained, and the
final search that shows none is left>

## Behaviour
<how it was shown unchanged: test counts, the probe compared, public
names compared; or what changed on purpose, and in which commit>

## Findings
<bugs, oddities and improvements seen and not acted on, each with its
evidence>
```

The `evals/` folder is for people testing this skill. Never open it
while doing a task.
