# Plan: the refactoring skill

Status: part 1 built (core, steps, legacy); recipes wait for architecture.
Built on branch `claude/skill-refactoring` as `skills/refactoring/`:
`SKILL.md`, `glossary.md`, `core/` (9), `steps/` (12), `legacy/` (4),
`tools/` (two scripts and their pages), `reference/` (2), `examples/`
(4), and `evals/` with 11 scenarios. The Reshape row of the router says
the recipes arrive with the architecture skill; `recipes/` and the
`service-from-router` eval are part 2. Sections 10 to 12 record what was
decided, verified and changed.

## 1. What it is

Changing the structure of code without changing what it does: pin the
behaviour, then small named steps, each checked and committed before the
next. It holds a catalogue of steps (rename, extract, move, inline,
split), recipes that walk code towards the architecture skill's target
shapes, and legacy-code techniques (characterization tests, seams). A
step that turns a check red is undone, not patched forward; a bug found
on the way is noted and fixed in its own commit. Like the other skills it
carries knowledge and judgement, not enforcement.

## 2. The environment it is written for

- **A weak model** (MiniMax 2.7 for evals) in Zed's agent on Windows
  with PowerShell, air gapped, Python through uv, the internal mirror
  only, no web.
- **No refactoring tools.** Zed's agent has `grep`, `find_path`,
  `read_file`, `edit_file`, `diagnostics` and `terminal`: no rename
  symbol, no move with import fixing, no find references. Every rename
  and move is search then edit, and must be proven complete: every hit
  listed, each edited or explained, then a check that fails on a miss.
- **Offline checks:** `uv run pytest`, ruff and a type checker if
  installed (linting says how), an import-every-module script, and
  seniority's behaviour probe. Which exist is checked, not assumed.
- **Windows traps**, to verify in the lab: a case-only file rename on a
  case-insensitive file system; edits that turn LF into CRLF.

## 3. The kinds of task

| Kind | Asked to | Answer shape |
| --- | --- | --- |
| **Plan** | say how to restructure something, without doing it | numbered steps, each named from the catalogue, with the check that closes it and what it pins first |
| **Step** | do one named refactoring: rename, extract, move, inline, split | the reference list (every hit, edited or explained), the diff, the checks run, one commit |
| **Reshape** | move code towards a target shape: service out of a router, a repository, separate DB and API models, feature layout | the step sequence taken, a commit per step, checks green after each |
| **Pin** | make untested code safe to change | characterization tests that pass now and fail when the code is broken, plus any seam added |
| **Tidy** | "clean up", "improve", "refactor" with no named result | seniority's narrow reading, the steps done, behaviour-unchanged evidence, findings not acted on |
| **Remove** | delete dead or unused code | per name: the searches run, what search cannot see, then removed or kept with the reason |
| **Untangle** | separate a change that mixes refactoring and behaviour change | two or more commits: structure only, then behaviour, each checked |

## 4. The failures it targets

| Failure | What it looks like |
| --- | --- |
| **Behaviour changed while "just refactoring"** | a default "tidied", an exception type changed, a sort made stable, rounding "fixed"; the report says no behaviour change |
| **Big-bang rewrite** | one edit touching twenty files; tests red for an hour; no point to go back to |
| **Incomplete rename** | the definition and direct calls renamed, but not `__all__`, `mock.patch("pkg.mod.old")` strings in tests, `getattr(obj, "old")`, dotted paths in config, entry points in `pyproject.toml`, docs |
| **Broken import path** | code moved to a new module; another package, a script or a plugin still imports the old path; nothing in the repository's tests covers it |
| **Refactor and fix in one step** | a bug fixed inside a move; the diff cannot be reviewed; when a test changes, nobody knows which half caused it |
| **Refactoring untested code blind** | no test covers the function; "tests pass" after the change because none ran it |
| **Deleting "dead" code that is alive** | a handler reached through a decorator registry, a string in YAML or an entry point is removed because grep found no call |
| **Fixing forward** | a step turns a check red and the model patches around it instead of undoing the step |
| **Characterization test that cannot fail** | asserts on a mock or on its own setup; passes with the code removed |
| **Contract renamed as structure** | a pydantic field, a route path or a stored Mongo field renamed; the JSON or the data changes; reported as a refactoring |

## 5. Layout

```
skills/refactoring/
  SKILL.md               router over the seven kinds, invariants, answers
  glossary.md            behaviour, public surface, seam, shim, pin
  core/
    before-you-start.md  pinned or not; baseline green; which checks exist
    plan-steps.md        cut a change into steps that each leave it working
    step-loop.md         edit, hunt references, check, commit; red: undo
    checks.md            after each step: import-all, lint, tests, probe
    every-reference.md   the rename and move hunt, on navigation's searches
    public-surface.md    what others rely on; when a shim is needed
    refactor-or-fix.md   a bug found on the way: note, pin, fix later
    dead-code.md         the evidence needed before a delete
    untangle.md          a mixed diff into structure and behaviour commits
  steps/                 the catalogue: preconditions, mechanics, traps
    rename.md  change-signature.md  extract-function.md
    inline-function.md  extract-variable.md  extract-class.md
    introduce-parameter-object.md  move-function.md  move-module.md
    split-module.md  replace-conditional.md  replace-magic-value.md
  recipes/               before and after trees, one commit per step, ran
    service-from-router/   logic out of a FastAPI route into a service
    introduce-repository/  data access behind a swappable repository
    split-model-schema/    DB model and API schema as separate classes
    layers-to-features/    layer folders to one folder per feature
  legacy/
    characterization.md  pin what the code does now, odd parts included
    golden-master.md     many outputs to a file, compared after each step
    seams.md             parameter, object, module seams; clock, IO
    sprout-and-wrap.md   new code beside old code not yet testable
  tools/import-all.md    a script that imports every module of a package
  examples/              a rename, a move with a shim, a pinned function
  evals/                 scenarios and sandboxes
```

Invariants, drafted: pin behaviour before the first edit; one step, one
check, one commit; red means undo; no behaviour change in a refactoring
commit; a rename is done when every hit is edited or explained and a
check that fails on a miss has run; a moved public name leaves a shim
unless every caller is in view.

## 6. Dependencies and boundaries

From the roadmap:

| Skill | Needs | Relies on by name | Existing skills it touches |
| --- | --- | --- | --- |
| refactoring | architecture | architecture, linting, git | pytest (characterization tests) |

| Ground | Owner | The other side |
| --- | --- | --- |
| layering rules (what a router, service, repository may do) | architecture | code-review turns them into checklist items; refactoring into recipes that fix them |
| the step-by-step change procedure | refactoring | code-review may suggest a refactoring; it does not perform one |

- **architecture** owns the target shapes: what a service, repository,
  DB model and API schema are and where each lives. Refactoring owns the
  route there: the order of steps, what each pins and checks. A recipe
  links to the architecture file for its end state, never restating it.
- **code-review** may say "extract a service here". Refactoring performs
  it, and does not review the result.
- **seniority** owns the behaviour-unchanged probe (scope question 6,
  done question 7) and the harness (`check_change.py`: snapshot,
  public-signature; `check_finish.py`: behaviour-unchanged). Refactoring
  adds no probe format or checker, only when to run the probe (after
  every step, not once at the end) and what it calls (the old import
  path, so a move is proven too).
- **git** owns the commands (staging named files, commit, `git restore`,
  `git mv`). Refactoring says when: a commit per green step, a restore on
  red, never a push.
- **linting** owns running ruff, mypy and pyright and reading them.
  Refactoring names the findings that mean a step broke something
  (undefined name, unresolved import, a missing name in `__all__`).
- **navigation** owns the searches (`core/trace-in.md`,
  `core/what-search-misses.md`). `every-reference.md` adds what a rename
  must also change and how to prove the list complete.
- **pytest** owns tests that can fail and patching where a name is used.
  `legacy/characterization.md` adds only asserting on today's output.

### Proposed changes to the roadmap

1. Add **navigation** and **seniority** (its harness) to refactoring's
   "Existing skills it touches": rename and move stand on them.
2. Split the build (RF1): only `recipes/` needs architecture; the rest
   needs linting and git (wave 1), so it can be built in wave 2.
3. New boundary rows: **proving every reference found** (navigation owns
   the searches, refactoring the rename checklist and proof); **a bug
   found during a refactoring** (debugging owns the fix, refactoring
   keeps it out of the refactoring commit); **renaming a serialized or
   stored name** (api and mongodb own the contract change or migration;
   it is not a refactoring).

## 7. How it will be verified

The lab, on the versions agreed under roadmap R2, must run:

- Every `steps/` file on a sample package, `core/checks.md` green after
  each step, and each trap reproduced: the missed `mock.patch` string,
  `__all__` entry and entry point.
- Every recipe from before tree to after tree, tests and linters green at
  every commit (`git rebase --exec` or a loop; to verify which).
- Which findings catch a broken move or rename on the pinned versions
  (expected: ruff F821, F822, F401; pyright's unresolved import; to
  verify in the lab). The import-all script on src and flat layouts.
- Seniority's harness on each recipe step. Expected from reading
  `check_change.py`: a move kept as a re-export, or a rename kept as an
  alias (`old = new`), is reported "removed or renamed", since it reads
  only top-level `def` and `class`; a split module fails `files-deleted`.
  To verify in the lab (RF4).
- The Windows traps from section 2, on Windows with PowerShell.
- Every eval below baited without the skill and passed with it.

## 8. Evals, written first

| Sandbox | Ask | Bait | Passes when |
| --- | --- | --- | --- |
| `tidy-pricing` | tidy `pricing.py` | an obvious rounding "fix" and a mutable default | probe identical before and after; both listed as findings, not edited |
| `big-module` | turn a 500-line module into a package | one sweeping edit | a commit per step, checks green at each; old imports still work |
| `rename-everywhere` | rename `get_user` to `fetch_user` | `__all__`, `mock.patch("app.users.get_user")`, `getattr(svc, name, None)` in a fallback, a dotted path in YAML, a docs page | every hit edited or explained; the silent `getattr` found |
| `move-util` | move `parse_date` into `dates.py` | a script in `tools/` and an entry point import the old path; no test covers them | shim kept or every importer changed; import-all run |
| `extract-with-bug` | extract the discount logic into a function | an off-by-one in the extracted lines | refactoring commit keeps the bug; bug reported, or fixed in a separate commit if asked |
| `legacy-report` | restructure `build_report` | no tests, reads the clock and a file | characterization test first, clock seam added, test fails with the code broken |
| `dead-handlers` | remove unused handlers | one reached by a decorator registry, one by name in YAML | both kept with evidence; truly dead ones removed |
| `schema-rename` | rename `user_name` to `username` in a model | the model is a response schema | declined as a contract change, or done with an alias and the JSON unchanged |
| `red-step` | extract a class | the second step turns a test red | the step is undone and redone smaller, not patched forward |
| `service-from-router` | move logic out of a route | a test overrides a dependency with `dependency_overrides` | the override still works; logic in a service; commits per step |

## 9. Decisions needed

### RF1. Build in two parts

*Recommended:* build `core/`, `steps/` and `legacy/` once linting and git
exist (wave 2), `recipes/` after architecture (wave 4). The catalogue
does not depend on target shapes; waiting holds back the most used part.

### RF2. Shims for moved or renamed public names

*Recommended:* change every caller when all are in the repository and
none come from outside (entry point, published package, other service).
Otherwise, or when unsure, keep a shim that re-exports the new name; a
`DeprecationWarning` only if the person asks.

### RF3. Scripted refactoring tools

*Recommended:* search and edit is the one path taught, since nothing
else is sure to be installed. `ruff check --fix` only for imports after
a step, as linting says; rope or libcst only if the mirror has them.

### RF4. The harness and correct refactorings

`check_change.py` would fail a move with a re-export or a rename with an
alias. *Recommended:* in the refactoring build, change the harness to
check that each old public name still imports from its old module with
the same signature, reviewed with seniority's owner.

### RF5. Commit granularity

*Recommended:* one local commit per green step, named after the
catalogue step. Squashing is the person's choice; never push.

### RF6. Characterization tests and languages

*Recommended:* keep characterization tests with the other tests, named
`test_characterize_*`; a pinned oddity carries a comment naming the
finding, so a later fix changes that test on purpose. Python only, as
the built navigation skill is; TypeScript later, if asked.

## 10. Decisions taken as defaults

- **RF1. Two parts.** Part 1 (core, steps, legacy, tools, reference,
  examples, evals) is built; `recipes/` and the `service-from-router`
  eval wait for the architecture skill. SKILL.md's Reshape row says so
  and, until then, sends a reshape through Plan and Step.
- **RF2. Shims.** Every caller changed only when all are in the
  repository and nothing outside names the old path; otherwise, or when
  unsure, a shim (`core/public-surface.md`), written as an explicit
  re-export (`from new import name as name`) because the lab showed
  ruff `--fix` deletes a plain one. No `DeprecationWarning` unless asked.
- **RF3. Search and edit only.** No rope or libcst (not assumed on the
  mirror). `ruff check --fix` only for imports, never on a module whose
  unused import is a shim. Two standard-library scripts replace what an
  IDE would check: `tools/import_all.py` and `tools/public_names.py`.
- **RF4. The harness.** Not changed in this build: roadmap R7 had
  already changed `check_change.py`. The lab confirmed what the change
  covers and recorded what it still misreads
  (`reference/change-check.md`, section 12); the gaps are reported to
  seniority's owner, not fixed here.
- **RF5. Commits.** One local commit per green step, named after the
  step; a red step is undone with a whole-tree stash; never a push.
- **RF6. Characterization tests** live with the other tests, named
  `test_characterize_*`, with a comment on each pinned oddity. Python
  only.

## 11. How it was verified

Python 3.12.14, pytest 9.1.1, ruff 0.16.9, mypy 2.3.1, pyright 1.1.414
(`pyright[nodejs]`), pydantic 2.13.5, PyYAML 6.0.3, git 2.43.0 and uv
0.8.17 (0.12.19, pinned for packaging, was not installed in this lab;
nothing here depends on the difference). PowerShell forms were run in
PowerShell 7.5.3 on Linux; nothing was run on Windows, and Windows-only
facts are marked `not run on Windows` or taken from CPython's source.

- Every eval's bait was reproduced and its intended fix run on a fresh
  copy of its sandbox: the naive rename (tests failed only on the patch
  string, ruff found only `__all__`, the `getattr` and YAML misses were
  silent), the move without a shim (only import-all found the script and
  the entry point), the split (the `CENT` loss, the patch-target red
  step, the circular import), the extraction with the off-by-one, the
  untested report, the handlers kept alive by a registry and a YAML
  route, the response field (JSON kept only by `alias` with
  `serialize_by_alias`), the red extract-class step, the mixed diff
  (5.0 against 4.99), and the tidy (probe identical, yet a dict lookup
  raised for an unhashable code).
- The steps were run on those sandboxes and on small scratch modules:
  rename (with and without an alias), move function, move module (with a
  `__main__` shim and `git log --follow`), split module (six commits,
  checked with `git rebase --exec`), extract function, variable and
  class, inline, introduce parameter object, change signature, replace
  conditional and magic value. Each trap in the `steps/` files is a
  recorded result.
- Which check sees which miss (`core/checks.md`) was measured on one
  package with every kind of broken reference, under ruff, mypy (with
  and without `--check-untyped-defs`) and pyright.
- `tools/import_all.py` ran on flat and `src` layouts, installed and not,
  with config files, scripts with and without a guard, and a `__main__`
  module; `tools/public_names.py` on every split step. Both pass ruff and
  `mypy --strict`.
- Seniority's `check_change.py` (RF4) ran on the lab's rename, move and
  split, and on a matrix of shim shapes and layouts.
- The four examples were replayed from fresh sandboxes, commands in
  PowerShell, and their output copied.

## 12. What the lab changed

Findings that corrected the plan or a common belief, each now in the
skill:

- **The harness after R7** (RF4). It passes a move re-exported with
  `from x import name` (absolute at the root or in `src/`, or relative),
  a class moved and re-exported, and a module split into a package; it
  still reports a changed default in the new place. It still reports as
  removed: a rename kept as an alias (`old = new`), a method alias in a
  class, a star re-export, an attribute shim (`f = mod.f`) and a module
  `__getattr__`. It reports a moved function's `except` without re-raise
  as a new swallowed error when the destination module existed before,
  and an assert line that only renamed the call as a changed
  expectation. It passes, wrongly, a re-export from a module that does
  not exist (treated as outside the working directory) and an absolute
  re-export in a package below `packages/<name>/src/`, even with a
  changed default. Reported for seniority's owner; the skill's
  `reference/change-check.md` says what to write in the answer.
- The plan expected ruff F821, F822 and F401 and pyright's unresolved
  import to catch broken renames and moves. They do, for their rows only:
  mypy says nothing about a stale `__all__`, and mypy without
  `check_untyped_defs` skips the bodies of unannotated functions, where
  pyright reports the same call. No checker sees `getattr` strings,
  dotted paths in config, entry points, patch targets or a circular
  import; import-all and the probe had to be added to every step.
- `__all__` is not the public surface: a public constant outside it was
  dropped by a split while every check was green.
- A shim written as a plain import is `F401 [*]` in a module (a safe fix
  that deletes it) but `F401` with no fix in an `__init__.py`.
- An alias keeps imports and calls working, not patches: a test that
  patched the old name no longer reached the code, and a subclass
  overriding the old method name was no longer called.
- Undoing a step with `git stash push -- <paths>` after a `git mv` saved
  a stash and then failed (`fatal: pathspec ... did not match any
  files`), leaving the change in both places. The skill stashes the
  whole tree and keeps the probe in an excluded `.ledger/`.
- A break-and-restore within one second, with the same file size, kept
  running the stale `.pyc` of the break; `PYTHONDONTWRITEBYTECODE=1` with
  no `__pycache__` made the loop reliable.
- A probe run as `python .ledger/probe.py` cannot import a flat project
  that is not installed; two lines at its top (`sys.path[:0] = ["",
  "src"]`) fix both layouts.
- An edited entry point is not seen by `uv run --no-sync` until the
  project is reinstalled (`uv sync`).
- A golden master over 53 dates caught a break (a threshold of 61 days
  instead of 60) that three characterization tests passed.
- Fixing the off-by-one in the extraction sandbox made ten items cost
  more (52.40 against 50.00), because shipping then applied: a reason,
  beyond reviewability, to keep a fix out of the refactoring and ask.

### For other skills and the roadmap

- **seniority** (harness): the RF4 gaps above. Also, read in the source
  and not run: `check_finish.py`'s `run_probe` runs the probe with the
  harness's own Python and `PYTHONPATH` set to the tree, so a probe of a
  `src` layout, or of code that needs the project's installed packages,
  may fail there although it runs under `uv run`.
- **navigation**: `core/search-patterns.md` could add the module form
  `from app import users` to its import pattern, which
  `^\s*(from|import)\s+[\w.]*\bbilling\b` does not match.
- **pytest**: `core/write-test.md` step 5 (make it fail) could mention the
  stale-bytecode trap for quick break-and-restore loops.
- **roadmap**: section 3's row for refactoring already lists navigation
  and seniority's harness; the boundary rows proposed in section 6 are
  in section 5. Nothing further.

