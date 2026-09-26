---
name: linting
description: Run ruff, mypy and pyright the way the project and CI run them, read what they report, and decide for each finding whether to fix the code, change the configuration or suppress one line. Lint, format, type check, fix a CI lint or type error, explain a ruff rule or mypy error code, noqa and type ignore comments, safe and unsafe fixes, per-file ignores, import sorting, ruff format against black, mypy strict mode and per-module overrides, missing imports and stubs offline, the pydantic mypy plugin, pyright and basedpyright, Zed's diagnostics panel, adding a checker to legacy code, and matching CI's versions. Also pre-commit in full - config, hook types and stages, commit-msg and pre-push hooks, hooks with no network, monorepos, CI, Windows - and a commit refused by a hook. Verified on ruff 0.16.9, mypy 2.3.1 and 1.20.2, pyright 1.1.414, basedpyright 1.40.1 and pre-commit 4.6.2.
---

# Linting

This skill knows how ruff, mypy, pyright and pre-commit behave, and
every command, option, config key and message in it was run on the
versions in the description, on Python 3.12. Never write a rule code,
error code, option or hook key from memory: find it here, or ask the
tool (`ruff rule <CODE>`, `ruff config <key>`, `ruff check
--show-settings`, `mypy --help`, `pyright --help`, `pre-commit <command>
--help`) and the installed source.

Read this file, then load only what the task needs.

## Read the versions first

```
uv tree --frozen --only-group dev --depth 1   # the versions in uv.lock
uv run --no-sync ruff --version               # ruff 0.16.9
uv run --no-sync mypy --version               # mypy 2.3.1 (compiled: yes)
uv run --no-sync pyright --version            # pyright 1.1.414
uv run --no-sync pre-commit --version         # pre-commit 4.6.2
```

The tool that counts is the one in `uv.lock`, which CI installs. A
`ruff` on `PATH` or `uvx ruff` may be another version, and ruff 0.16
enables seven times as many rules by default as 0.15
(`core/run-like-ci.md`). `mypy/versions.md` lists what changed from
mypy 1.x to 2.x.

## The kinds of task

| Kind | You were asked to | Load |
| --- | --- | --- |
| **Run** | run the checks as CI does | `core/run-like-ci.md`, `core/config-files.md` |
| **Read** | explain a finding | `core/read-finding.md`, then `ruff/rules.md`, `mypy/errors.md` or `pyright/errors.md` |
| **Fix** | make the checks pass for a change | `core/in-scope.md`, `core/decide.md`, `ruff/fixes.md` |
| **Suppress** | silence one finding | `core/decide.md`, then `ruff/suppression.md`, `mypy/suppression.md` or `pyright/suppression.md` |
| **Configure** | tune rules, strictness, a plugin | `core/config-files.md`, then `ruff/config.md`, `mypy/strictness.md`, `mypy/pydantic.md` or `pyright/config.md` |
| **Adopt** | bring a checker or stricter mode to legacy code | `core/adopt.md`, `mypy/strictness.md` |
| **Match CI** | local and CI disagree; the editor panel disagrees | `core/run-like-ci.md`, `core/zed.md` |
| **Format** | format code, or move from black to `ruff format` | `core/in-scope.md`, `ruff/format.md`, `ruff/imports.md` |
| **Imports** | a checker cannot find a module or its types | `mypy/stubs.md`, `pyright/install.md` |
| **Pre-commit** | set up, extend or repair hooks: offline, per stage, per folder of a monorepo | `pre-commit/config.md`, `pre-commit/offline.md`, `pre-commit/install.md`, then `pre-commit/monorepo.md` or `pre-commit/windows.md` |
| **Hook blocked** | a commit is refused, or a hook changed files | `pre-commit/blocked.md`, `pre-commit/run.md` |
| **Hooks in CI** | run the same hooks in a pipeline | `pre-commit/ci.md` |

## Where the facts are

| Folder | Holds |
| --- | --- |
| `core/` | the procedures above |
| `ruff/` | rule selection and the default set, fixes and their safety, config files and `extend`, import sorting, the formatter against black, suppression comments |
| `mypy/` | reading errors, strict mode and overrides, missing imports and stubs offline, the pydantic plugin, `type: ignore`, mypy 2 against 1.x |
| `pyright/` | reading errors, modes and strict paths, config files, `pyright: ignore`, installing it without Node, basedpyright |
| `pre-commit/` | config and YAML traps, hooks with no network, installing, running, a refused commit, monorepos, CI, the catalogue of hooks and who owns each, Windows, prek |
| `recipes/` | configs that ran: `pre-commit-project/` and `pre-commit-workspace/` (offline hooks), `pyproject/` (ruff, mypy and pyright tables) |
| `examples/` | four finished tasks: a newer global ruff (`global-ruff.md`), a type error fixed by narrowing (`narrow-not-cast.md`), a commit refused by a hook (`refused-commit.md`), hooks made to work offline (`offline-hooks.md`) |

`glossary.md` fixes the words.

## Invariants

1. **The lock's tools, run the way CI runs them.** `uv run --no-sync
   <tool>` (or `uv run --frozen` in hooks), after checking the version
   against `uv.lock`; never a global tool as the verdict.
2. **The meaning of a code comes from the tool**, `ruff rule <CODE>`,
   mypy's code, pyright's rule name, never from memory.
3. **Fix first, configure second, suppress one line last**, and a
   suppression always names its code and gives a reason. Never a bare
   `# noqa`, `# type: ignore`, `# pyright: ignore` or `# ruff: noqa`.
4. **A type error is fixed in the value, not hidden.** No `cast`, `Any`,
   widened annotation or ignore to quiet a true error.
5. **The task's lines only.** Formatting or fixing the rest of the
   repository is its own commit, done when the person agrees.
6. **Unsafe fixes are read before they are applied** (`--diff
   --unsafe-fixes`), and the tests run after.
7. **The config file that counts is the one the tool says it read**
   (`--show-settings`, `mypy -v`, `pyright --verbose`).
8. **A refused commit is a finding.** Never `--no-verify`, `-n` or
   `SKIP=` unless the person asked for exactly that hook to be skipped.
9. **Nothing is installed to make a check pass.** Air gapped, `pip
   install types-x`, `--install-types` and a new plugin cannot work.
10. **CI is the standard; the editor panel is a hint.** Read what the
    panel says, but do not rewrite code to empty it.

## What you say when you finish

End with these headings, each with `none` when empty. If another skill
is loaded, its headings come first and these after.

```
## Result
<what changed, or the finding explained, with paths and codes>

## Checked
<each tool's version, and each command run with its summary line, such
as "All checks passed!" or "Success: no issues found in 4 source files">

## Not checked
<checkers or versions not run, CI not seen, platforms not tried>
```

The `evals/` folder is for people testing this skill. Never open it
while doing a task.
