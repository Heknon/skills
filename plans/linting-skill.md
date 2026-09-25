# Plan: the linting skill

Status: draft for decision. Nothing is built yet.

## 1. What it is

The knowledge to run ruff, mypy and pyright the way the project and its
CI run them, read what they report, and decide for each finding whether
to fix the code, change the configuration, or suppress that one line.
It covers ruff as linter and formatter (rule selection, `ruff rule`,
safe and unsafe fixes, per-file ignores, `extend`, import sorting, how
`ruff format` differs from black), mypy and pyright (reading errors,
strictness, gradual adoption on legacy code, missing imports and stubs
offline, the pydantic mypy plugin, `reveal_type` to debug an error),
where each tool reads its configuration, matching CI's versions, and
pre-commit with no network. It carries knowledge and judgement, not
enforcement.

## 2. The environment it is written for

- **A weak model in Zed's agent on Windows, PowerShell, air gapped.**
  No rule documentation site. The skill teaches the offline sources:
  `ruff rule <CODE>`, `ruff linter`, `ruff check --show-settings`,
  `mypy --help`, pyright's `--verbose`, and the installed source.
- **Python through uv, packages from an internal mirror.** The checker
  that counts is the one in `uv.lock`, run with `uv run --no-sync`. A
  global `ruff` on `PATH` or `uvx ruff` may be another version.
- **Zed's diagnostics panel** shows the Python language servers Zed
  starts, with their own defaults where the project has no config.
  Which ones start by default (pyright, basedpyright, ruff, ty) is to
  verify in the lab. CI is the standard; the panel is a hint.
- **pre-commit cannot fetch hook repositories offline.** Every
  `repo: https://...` entry fails on first use.
- **pyright is a Node program.** The PyPI wheel carries the JavaScript
  but, without its `nodejs` extra, fetches Node through `nodeenv` from
  the web; `pyright[nodejs]` takes it from `nodejs-wheel-binaries` in
  the mirror. Offline behaviour of both is to verify in the lab.

## 3. The kinds of task

| Kind | Asked to | Answer shape |
| --- | --- | --- |
| **Run** | run the checks as CI does | the command, the tool versions, the output |
| **Read** | explain a finding | the code, its meaning from `ruff rule` or the checker, the line |
| **Fix** | make the checks pass for a change | a diff limited to the change, then clean output from the same command |
| **Suppress** | silence one finding | one comment with the code and a reason, and why fixing was wrong |
| **Configure** | tune rules, strictness, a plugin | the edit in the file the tool reads, and the tool's proof it read it |
| **Adopt** | bring a checker or stricter mode to legacy code | the config, error counts per module before and after, the next step |
| **Match CI** | local and CI disagree | versions and config on each side, the difference |
| **Format** | format code, or move from black to `ruff format` | the scope formatted, the diff size, differences from black named |
| **Imports** | a checker cannot find a module or its types | the environment it used, what is installed, the narrowest setting |
| **Pre-commit** | set up or repair hooks offline | `.pre-commit-config.yaml` with local hooks, a run's output |

## 4. The failures it targets

| Failure | What it looks like |
| --- | --- |
| **Blanket suppression** | bare `# noqa`, `# type: ignore` or `# pyright: ignore` with no code; a file-level `# ruff: noqa` |
| **Silencing with types** | `Any`, `cast(...)` or a widened annotation to quiet mypy, instead of narrowing or fixing the value |
| **Reformatting the world** | `ruff format .` or `ruff check --fix .` over the repository inside an unrelated change |
| **Fixing a disabled rule** | rewriting code for a rule the project ignores, after `--select ALL` or trusting Zed's panel |
| **Trusting unsafe fixes** | `--fix --unsafe-fixes` applied without `--diff`, changing behaviour |
| **Wrong version** | a global ruff or mypy that differs from `uv.lock` and CI; the model "fixes" the noise |
| **Config silently ignored** | `[tool.ruff]` edited while a `ruff.toml` wins; `[tool.mypy]` edited while `mypy.ini` exists; a key in the wrong table |
| **Global escape hatch** | `ignore_missing_imports = true` or `ignore_errors` for everything, to clear one error |
| **Rule meaning from memory** | explains a code it never looked up; codes are renamed between versions |
| **Installing to fix** | `pip install types-x` or a new plugin, which cannot work air gapped |

## 5. Layout

```
skills/linting/
  SKILL.md           router over the ten kinds, invariants; glossary.md
  core/
    run-like-ci.md   find CI's command, versions, config; run the same
    read-finding.md  from an output line to the code, meaning, cause
    decide.md        fix, configure or suppress; suppress narrowly
    in-scope.md      fix changed lines only; formatting on its own
    config-files.md  which file each tool reads, precedence, proof
    adopt.md         legacy code: counts, per-module settings, ratchet
    zed.md           which server feeds the panel; why it disagrees
    pre-commit.md    local hooks through uv, nothing fetched
  ruff/
    rules.md         select, extend-select, preview, ruff rule
    fixes.md         safe and unsafe fixes, --diff, per-rule settings
    config.md        extend, per-file-ignores, hierarchy
    imports.md       the I rules in place of isort, first-party
    format.md        ruff format, differences from black, --check
    suppression.md   noqa with codes, RUF100, PGH004, file level
  mypy/
    errors.md        reading output, codes, notes, reveal_type
    strictness.md    what --strict turns on, per-module overrides
    stubs.md         missing modules offline, py.typed, mirror stubs
    pydantic.md      the plugin: enabling it, settings, what changes
    suppression.md   type: ignore[code], unused and codeless ignores
    versions.md      what mypy 2 changed for a 1.x codebase
  pyright/
    errors.md        report rules, severities, reading output
    strictness.md    typeCheckingMode, strict paths, file comments
    config.md        pyrightconfig.json against [tool.pyright]
    suppression.md   pyright: ignore[rule], unnecessary ignores
    install.md       pyright[nodejs], basedpyright, no-Node errors
  recipes/           configs that ran, pre-commit local hooks included
  examples/          worked tasks with the real commands and output
  evals/             scenarios and sandboxes
```

## 6. Dependencies and boundaries

| Skill | Needs | Relies on by name | Existing skills it touches |
| --- | --- | --- | --- |
| linting | none | pydantic (checker errors on models) | pytest (config in `pyproject.toml`) |

- **Needs none**, so it builds in wave 1.
- **pydantic, by name.** Linting owns running the checkers, their
  config, and the pydantic mypy plugin setting (`plugins =
  ["pydantic.mypy"]` and `[tool.pydantic-mypy]`: `init_typed`,
  `init_forbid_extra`, `warn_required_dynamic_aliases`). pydantic owns
  what a model's types mean: `Annotated`, generics, discriminated
  unions, `Optional` against a default. When mypy complains about a
  model, linting checks the plugin is on and the error is real, then
  points at pydantic for why the type is what it is.
- **pytest, touched.** Both configure in `pyproject.toml`. Linting owns
  the ruff, mypy and pyright tables, test settings included (such as
  `per-file-ignores` for `tests/**`); never `[tool.pytest]`.
- **code-review needs linting.** What the three tools catch is
  linting's. code-review runs the project's tools and reads the output;
  it does not repeat their checks as checklist items.
- **refactoring relies on linting**, to run the checkers after a step.

### Proposed changes to the roadmap

1. **navigation, touched**, and a boundary row: navigation owns asking
   a checker for a type (the `reveal_type` probe, environment flags);
   linting owns what an error means, config, strictness, and the lasting
   setting behind navigation's one-off missing-import flags.
2. **deployment, touched.** Its CI component runs `uv run --no-sync
   ruff check` and `ruff format --check`. Deployment owns the job;
   linting owns what it checks and matching it locally.
3. **documentation, touched.** It reads the docstring style from
   `[tool.ruff.lint.pydocstyle]`; linting owns that setting.
4. **offline-docs, by name**: whether an installed package ships
   `py.typed` or stubs, and which version is installed.
5. **A `pyproject.toml` row.** packaging owns `[project]`,
   `[build-system]` and the dependency groups that pin ruff and mypy;
   each tool's table belongs to that tool's skill.
6. **git, by name.** A formatting-only commit and
   `.git-blame-ignore-revs` are git's; linting says when to use them.

## 7. How it will be verified

Pinned, from versions seen on 2026-09-25 (to confirm against what the
air-gapped mirror carries): ruff 0.16.9, as in deployment's `uv.lock`;
mypy 2.3.1, and 1.20.2 if L2 is accepted; pyright 1.1.414, as
navigation, with `nodejs-wheel-binaries` 24.19.0, and basedpyright
1.40.1 if Zed uses it; Python 3.12, as pytest; pydantic 2.13.5, to
agree with the pydantic plan (R2); black 26.5.1 for the comparison;
pre-commit 4.6.2.

The lab, with the network off, must run every command, flag and
config key in the skill and record the output it quotes; put two config
files side by side for each tool and record which wins (precedence is
not written from memory); confirm `ruff rule`, `ruff linter` and
`--show-settings` work offline; apply each unsafe fix the skill names;
diff black and `ruff format` on one sample; run mypy with and without
the pydantic plugin on the same models; run pyright with and without
the `nodejs` extra; run pre-commit with a local and a remote hook;
check PowerShell quoting of globs and paths; and start Zed to record
which Python servers feed its panel.

## 8. Evals, written first

Each a small uv project with its lock, baiting one failure. A pass needs
the named evidence, not only clean output.

1. **noqa-code.** An unused import that is a re-export. Pass: a fix, or
   `# noqa: F401` with a reason. Fail: bare `# noqa`.
2. **narrow-not-cast.** mypy `arg-type` on `str | None`. Pass: a
   `None` check. Fail: `cast`, `Any` or `type: ignore`.
3. **one-function.** Thirty unformatted files; a bug in one function.
   Pass: the diff touches that function only.
4. **disabled-rule.** `E501` ignored; "tidy lint in `app/report.py`".
   Pass: long lines left alone.
5. **unsafe-fix.** An unsafe fix changes behaviour and a test catches
   it. Pass: `--diff` read, the fix declined or done by hand.
6. **ci-version.** `uv.lock` pins an older ruff, a newer one is on
   `PATH`, a CI log is given. Pass: versions compared before any edit.
7. **wrong-config.** Both `ruff.toml` and `[tool.ruff]`; "ignore S101
   in tests". Pass: edits the file that wins, shows `--show-settings`.
8. **pydantic-plugin.** mypy misreads a model's `__init__`. Pass: the
   plugin enabled in config. Fail: `type: ignore`.
9. **untyped-internal.** `import-untyped` on an internal package. Pass:
   a per-module override. Fail: a global setting or `pip install`.
10. **legacy-adopt.** 200 mypy errors; "add mypy to CI". Pass: strict
    for new modules, legacy listed, counts recorded.
11. **pre-commit-offline.** Hooks from GitHub URLs fail. Pass: `local`
    hooks through `uv run --no-sync`, and a run's output.
12. **zed-panel.** The prompt pastes pyright findings from Zed; CI runs
    only mypy. Pass: names what CI runs; no rewrite for the other.

## 9. Decisions needed

- **L1. Which checkers.** ty 0.0.84 is in the mirror and navigation
  reads types with it. *Recommended:* ruff, mypy and pyright; ty gets
  a note on its config and ignore comment, and a folder at 1.0.
- **L2. mypy 1.x as well as 2.x.** *Recommended:* write against 2.3.1;
  `mypy/versions.md` records what differs on 1.20.2, since legacy
  projects may still pin 1.x.
- **L3. How pyright runs offline.** *Recommended:* `pyright[nodejs]`
  from the mirror, through uv, with basedpyright as the documented
  alternative. Settle it in the lab.
- **L4. Suppression form.** *Recommended:* always a code and a reason
  on the line, such as `# noqa: F401  re-exported for plugins` or
  `# type: ignore[arg-type]  # stub is wrong`. The skill suggests
  `PGH004`, `RUF100`, `warn_unused_ignores` and `ignore-without-code`;
  it does not add them to a project unasked.
- **L5. An unformatted repository.** *Recommended:* never formatted
  inside another change. Format what the task touches, and offer one
  formatting-only commit listed in `.git-blame-ignore-revs`.
- **L6. Gradual adoption.** *Recommended:* per-module overrides with a
  written ratchet. `ruff check --add-noqa` is documented and used only
  when the person asks for a baseline.
- **L7. pre-commit hooks.** *Recommended:* `repo: local` hooks running
  `uv run --no-sync ruff` and `mypy`, so the version is the lock's and
  CI's. Hooks from an internal Git mirror are the alternative.
