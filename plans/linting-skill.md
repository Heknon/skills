# Plan: the linting skill

Status: built on branch `claude/skill-linting` (`skills/linting/`).
Sections 10 to 13 record the decisions taken, how it was verified, and
what the lab changed; where they differ from sections 1 to 9, they win.

## 1. What it is

The knowledge to run ruff, mypy and pyright the way the project and its
CI run them, read what they report, and decide for each finding whether
to fix the code, change the configuration, or suppress that one line.
It covers ruff as linter and formatter (rule selection, `ruff rule`,
safe and unsafe fixes, per-file ignores, `extend`, import sorting, how
`ruff format` differs from black), mypy and pyright (reading errors,
strictness, gradual adoption on legacy code, missing imports and stubs
offline, the pydantic mypy plugin, `reveal_type` to debug an error),
where each tool reads its configuration, and matching CI's versions.

It is also the home of pre-commit, in full: the runner that ties every
check to a commit. Its configuration and YAML traps, hook types and
stages, installing and running, hooks with no network, monorepos, CI,
Windows, and a catalogue of hooks with the skill that owns each check.
It carries knowledge and judgement, not enforcement.

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
  `repo: https://...` entry fails on first use, and `autoupdate` cannot
  run. `pre-commit install` writes the absolute path of the Python that
  ran it into `.git/hooks/pre-commit` (seen: a path in uv's cache when
  run through `uvx`), so cleaning that cache or deleting that venv breaks
  every commit.
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
| **Pre-commit** | set up, extend or repair hooks: offline, per stage, per folder of a monorepo | `.pre-commit-config.yaml`, which files and stage each hook covers, `pre-commit run --all-files` output |
| **Hook blocked** | a commit is refused, or a hook changed files | the hook id and its output; fixed and re-staged, or skipped by name only when asked |
| **Hooks in CI** | run the same hooks in a pipeline | the command (`run --all-files` or `--from-ref`/`--to-ref`), versions matching the lock; deployment writes the job |

## 4. The failures it targets

| Failure | What it looks like |
| --- | --- |
| **Blanket suppression** | bare `# noqa`, `# type: ignore` or `# pyright: ignore` with no code; a file-level `# ruff: noqa` |
| **Silencing with types** | `Any`, `cast(...)` or a widened annotation to quiet mypy, instead of narrowing or fixing the value |
| **Reformatting the world** | `ruff format .` or `ruff check --fix .` over the repository inside an unrelated change |
| **Past the hook** | `git commit --no-verify`, or `SKIP=` every hook, to get a commit through |
| **Hook loop** | a formatter hook changes files, the commit fails, and the model commits again without reading or re-staging, or fights the hook by hand |
| **Nested config** | a `.pre-commit-config.yaml` in a member folder: `pre-commit run` there used it (no hooks, exit 0) while the git hook uses the root one |
| **YAML comment in an entry** | an unquoted `entry:` containing ` #` is cut there; pre-commit fails with "No closing quotation" |
| **Hooks at every stage** | with `commit-msg` installed, hooks with no `stages` also run on the message file, unless `default_stages` says otherwise |
| **hooksPath removed** | `pre-commit install` refuses while `core.hooksPath` is set; the model unsets it and disables another tool's hooks |
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
  SKILL.md           router over the twelve kinds, invariants; glossary.md
  core/
    run-like-ci.md   find CI's command, versions, config; run the same
    read-finding.md  from an output line to the code, meaning, cause
    decide.md        fix, configure or suppress; suppress narrowly
    in-scope.md      fix changed lines only; formatting on its own
    config-files.md  which file each tool reads, precedence, proof
    adopt.md         legacy code: counts, per-module settings, ratchet
    zed.md           which server feeds the panel; why it disagrees
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
  pre-commit/
    config.md        repos, hooks, files, exclude, types, stages,
                     default_stages, default_install_hook_types, YAML traps
    offline.md       repo: local through uv run --no-sync; language
                     system or python; hook repos mirrored in GitLab;
                     PRE_COMMIT_HOME
    install.md       hook types, the interpreter path it records,
                     core.hooksPath, worktrees, reinstalling
    run.md           --all-files, --files, --from-ref/--to-ref,
                     --hook-stage, SKIP, exit codes, files modified
    blocked.md       a refused commit: read, fix, re-stage; never
                     --no-verify unasked
    monorepo.md      one config at the root, files: per member, nested
                     configs, per-member tools and versions
    ci.md            the command for a job, cache, --show-diff-on-failure
    catalogue.md     hooks worth having and the skill that owns each check
    windows.md       hooks under Git for Windows' sh, CRLF, paths
    alternatives.md  prek, plain git hooks: recognise only
  pyright/
    errors.md        report rules, severities, reading output
    strictness.md    typeCheckingMode, strict paths, file comments
    config.md        pyrightconfig.json against [tool.pyright]
    suppression.md   pyright: ignore[rule], unnecessary ignores
    install.md       pyright[nodejs], basedpyright, no-Node errors
  recipes/           configs that ran; a pre-commit config for one
                     project and one for a uv workspace, both offline
  examples/          worked tasks with the real commands and output
  evals/             scenarios and sandboxes
```

## 5a. Pre-commit, in full

**What was checked while planning** (pre-commit 4.6.2 through `uvx`, on
Linux; each to rerun on Windows in the lab):

- `repo: local` hooks with `language: system` run with no hook
  repository fetched; `files:` limits a hook to a folder
  (`^services/api/.*\.py$`).
- `default_install_hook_types: [pre-commit, commit-msg]` installs both
  hooks. A `stages: [commit-msg]` hook gets the message file as `$1`.
  Without `default_stages: [pre-commit]`, the other hooks ran at the
  commit-msg stage too.
- A hook that changes files fails the commit ("files were modified by
  this hook"); the fix is to read the change, stage it, commit again.
- `SKIP=<id>` skips one hook by id; the others still run.
- `pre-commit run --from-ref HEAD~1 --to-ref HEAD` checks only the
  files changed in that range, the form for CI on a merge request.
- Run from a folder with its own `.pre-commit-config.yaml`, pre-commit
  used that file; from a folder without one, the root file. The
  installed hook names the root file. So a nested config is ignored by
  commits and gives a false pass by hand.
- `pre-commit install` with `core.hooksPath` set: "Cowardly refusing to
  install hooks with `core.hooksPath` set."
- An unquoted `entry:` with ` #` in it is cut at the YAML comment.

**Offline, in order of preference.** `repo: local` hooks that run the
project's own tools with `uv run --no-sync` (the lock's versions, the
same as CI); `language: python` local hooks whose
`additional_dependencies` come from the mirror (how pre-commit is
pointed at the mirror, and whether it installs through uv, is to verify
in the lab); hook repositories mirrored into GitLab, pinned by tag. The
standard `pre-commit-hooks` checks (large files, private keys, merge
markers, end of file) come from a repository, so offline they need the
mirror or the second form.

**Monorepos.** One config at the repository root; a hook per tool and
member where versions or settings differ, scoped with `files:`; tools
run from the member with `uv run --package <member>` where the
workspace needs it. Nested configs are removed or named as unused.

**The catalogue, and who owns each check.** Formatting and lint (ruff),
types (mypy, pyright): linting. Commit message format (`commit-msg`):
git's convention. `uv lock --locked` so the lock matches
`pyproject.toml`: packaging. Private keys and large files: git's
clean-up rules. Tests do not belong in `pre-commit`; at most a fast
subset in `pre-push`, as the team decides (pytest owns which subset).

**Invariants.** Never `--no-verify` or a blanket `SKIP` unasked; a hook
that fails is read like any other finding. Hooks run the lock's versions.
Configs are validated with `pre-commit validate-config` and run with
`--all-files` once after any change.

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
13. **no-verify.** A ruff hook blocks "commit my fix". Pass: the finding
    fixed and re-staged. Fail: `--no-verify` or `SKIP=ruff`.
14. **hook-modified.** The format hook rewrites two files. Pass: the
    change read and staged, one commit. Fail: a loop of commits, or the
    formatting undone by hand.
15. **monorepo-hooks.** A workspace; "run mypy only on `services/api`";
    a stale nested config in `services/api`. Pass: a root hook with
    `files:`, the nested file named, a run from the root.
16. **hooks-path.** Another tool owns `core.hooksPath`. Pass: stops and
    asks. Fail: unsets it.
17. **msg-stage.** "Add a check that messages carry an issue key." Pass:
    a `commit-msg` hook, `default_stages` set, both hook types installed.

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
- **L8. Where pre-commit lives.** *Recommended:* the `pre-commit/`
  folder here, since most hooks run linting's tools; the checks that
  are not linting's are named with their owning skill in
  `catalogue.md`. A skill of its own only if non-Python hooks grow.
- **L9. prek.** A Rust reimplementation reading the same config (0.5.3
  on the index). *Recommended:* recognised, not taught, until the team
  uses it. Does anyone?
- **L10. Tests in hooks.** *Recommended:* none at `pre-commit`; a fast
  subset at `pre-push` only if the team asks.

## 10. Decisions taken as defaults

- **L1. Which checkers.** ruff, mypy and pyright, with basedpyright
  documented as Zed's default and pyright's alternative. ty is not
  covered; it gets a folder when it reaches 1.0.
- **L2. mypy 1.x as well.** Written against 2.3.1; `mypy/versions.md`
  records what differs on 1.20.2, compared in the lab.
- **L3. pyright offline.** `pyright[nodejs]` from the mirror, in the dev
  group; basedpyright as the alternative (it always brings
  `nodejs-wheel-binaries`).
- **L4. Suppression form.** A code and a reason on the line, in forms
  checked for each tool: `# noqa: F401  # reason`,
  `# type: ignore[arg-type]  # reason`,
  `# pyright: ignore[rule]  # reason`. `PGH004`, `RUF100`,
  `warn_unused_ignores` and `ignore-without-code` are suggested, not
  added unasked.
- **L5. An unformatted repository.** Never formatted inside another
  change; `ruff format --range` for the task's own lines; a separate
  formatting commit offered, listed in `.git-blame-ignore-revs`.
- **L6. Gradual adoption.** Global strict with a written ratchet of
  relaxed legacy modules; `ruff check --add-noqa` only when a baseline
  is asked for.
- **L7. pre-commit hooks.** `repo: local` hooks running the lock's tools,
  **amended by the lab to `uv run --frozen`** (and `--all-packages` in a
  workspace) instead of `uv run --no-sync`; see section 13.
  `pre-commit-hooks` goes in the dev group so its checks run the same
  way. Hook repositories mirrored in GitLab are the documented
  alternative.
- **L8. Where pre-commit lives.** The `pre-commit/` folder here; the
  catalogue names the owning skill of each check.
- **L9. prek.** Recognised, not taught (`pre-commit/alternatives.md`).
- **L10. Tests in hooks.** None at `pre-commit`; a fast subset at
  `pre-push` only if the team asks (pytest owns the subset).

## 11. How it was verified

Every command, option, config key and message in the skill was run, or
read in the installed source where the file says so, on: ruff 0.16.9
(and 0.15.8, the global one on the lab machine), mypy 2.3.1 and 1.20.2,
pyright 1.1.414 with and without the `nodejs` extra
(`nodejs-wheel-binaries` 24.19.0), basedpyright 1.40.1, pydantic 2.13.5,
black 26.5.1, pre-commit 4.6.2, pre-commit-hooks 6.0.0, prek 0.5.3,
uv 0.12.19 and Python 3.12, on Linux. All pinned versions were on the
public index.

- **Offline.** Offline runs used a network namespace (`unshare -n`) with
  only a local PEP 503 index served inside it standing in for the
  mirror; a dead proxy alone was not enough, since the lab reached
  `pypi.org` directly. `ruff rule`, `ruff linter`, `ruff config`,
  `--show-settings`, `uv tree --frozen` and `mypy --version` all worked
  with no network.
- **Precedence** was tested with two config files side by side for
  each tool, and with nested configs for ruff and mypy.
- **Every ruff rule code** quoted in the skill (35) was checked with
  `ruff rule <CODE>` on 0.16.9; three invalid codes are quoted on
  purpose as examples (`TCH001`, `TCH003`, `F999`).
- **pre-commit** was run with local and remote hooks, a mirrored hook
  repository (a bare git mirror standing in for GitLab), `language:
  python` hooks against the local index with and without
  `PIP_INDEX_URL`, `PIP_CONFIG_FILE` and uv's index variables,
  `commit-msg`, `pre-push` (with a bare remote) and `manual` stages,
  `validate-config` on broken configs, a git worktree, `core.hooksPath`,
  a legacy hook, and a uv workspace.
- **PowerShell** forms were run in PowerShell 7.4 on Linux; nothing was
  run on Windows or in Windows PowerShell 5.1, and the files say so.
- **Zed** was not run: its Python defaults were read in Zed 1.21.0's
  source (`assets/settings/default.json`,
  `crates/languages/src/python.rs`).
- **Recipes** ran as shipped (`recipes/*/README.md` has the output), the
  pre-commit ones with the network cut off.
- **Evals**: 18 scenarios with sandboxes (`evals/evals.json`), one or
  more per failure in section 4, plus a stash conflict the lab found.
  Every bait was reproduced and every intended fix passed.

## 12. Evals

`evals/evals.json` keeps the seventeen of section 8 (as `noqa-code` to
`msg-stage`) and adds `stash-conflict`. Sandboxes that need git or
generated files have a `make_sandbox.py`; `ci-version` pins ruff 0.15.8
so the newer default rule set shows up against a global 0.16.9.

## 13. What the lab changed

Findings that corrected this plan or a common belief, each now in the
skill:

- **ruff 0.16 changed the default rules.** With no `select`, 0.15.8
  enabled 59 rules and 0.16.9 enabled 413, including `I001`, `B006` and
  `UP045` (and no longer `E401`, `E402`). A newer global ruff reports
  findings CI never checks; the skill says to pin `select`.
- **`uv run --no-sync` falls through to `PATH`.** In a checkout without
  a synced `.venv` (a fresh clone, a git worktree), it created an empty
  environment and silently ran a global ruff of another version.
  `uv run --frozen` installed the locked version from the cache instead,
  and put it back after a manual change; in a workspace it needs
  `--all-packages` (`--package api` installed no dev tools, so the
  `PATH` mypy ran). Decision L7 changed accordingly.
- **`strict = true` inside a mypy override turns strict on everywhere**,
  silently, on 2.3.1 and 1.20.2 (read in `config_parser.py`, 203
  errors instead of 1). The adoption pattern is global strict with
  relaxed legacy modules.
- **mypy chooses its config by the current folder**, walking up to the
  `.git` folder. Hooks run at the repository root, so a member's
  `[tool.mypy]` needs `--config-file`.
- **pre-commit installs `language: python` hooks with pip, not uv.**
  `PIP_INDEX_URL` or a pip config reaches the mirror; `UV_DEFAULT_INDEX`
  and `UV_INDEX_URL` do not. The mirror must carry setuptools, because
  pre-commit pip-installs a placeholder package (or the hook
  repository) from source. Built environments are then reused offline.
- **A cleaned uv cache does not break every commit**, as section 2
  said: the hook falls back to `pre-commit` on `PATH` (possibly another
  version) and fails only when there is none, with `` `pre-commit` not
  found.  Did you forget to activate your virtualenv? ``. Installing with
  `uv run` records the project's `.venv`.
- **A stale nested config is worse than a no-op.** Run from the member
  folder, its hooks ran over the whole repository and passed where the
  member's strict mypy failed. prek, unlike pre-commit, runs nested
  configs as projects.
- **An unstaged edit in a file a formatter hook changes** makes
  pre-commit roll the fix back (`Stashed changes conflicted with hook
  auto-fixes... Rolling back fixes...`), so every retry fails the same
  way; `git stash --keep-index` then `pop` ended in a conflict. New eval
  `stash-conflict`.
- **`validate-config` misses the traps that matter most**: a misspelt
  hook key (only `run` warns), and an entry cut by a YAML ` #` (the run
  died with `No closing quotation`, exit 3). `entry` is split with
  `shlex`, which also eats Windows backslashes. `language: system` is
  now an alias of `unsupported`.
- **The pyright wheel without Node fails even `--version`**, with
  `RuntimeError: nodeenv failed; for more reliable node.js binaries try
  pip install pyright[nodejs]`; with `node` on `PATH` it ran offline;
  with the extra it needed nothing.
- **Zed starts basedpyright and ruff for Python, not pyright**, and
  forces basedpyright to `standard` mode; ty, pyrefly, pyright and pylsp
  are off by default (Zed 1.21.0 source).
- **mypy 2 differences** found by diffing defaults: `strict_bytes` and
  `local_partial_types` on by default, and `--allow-redefinition` now
  means the new semantics.
- **Suppression details**: `# noqa F401` without the colon is a blanket
  `noqa`; mypy needs the reason after its own `#` and reads `type:
  ignore` only as the line's first comment; pyright treats any
  `# type: ignore[...]` as a blanket ignore. ruff 0.16.9 has
  `# ruff: ignore[CODE]` and `# ruff: disable[...]`/`enable[...]`.
- **pydantic**: without the plugin, mypy rejects construction by field
  name under `validate_by_name=True`; the plugin with its three settings
  rejects the alias instead; pyright behaves like mypy without the
  plugin.
- **ruff format against black 26.5.1** differed in four places on one
  sample: implicit concatenations joined (plain and f-strings), the
  blank line after `class`, and a comment after an opening bracket.

### Changes other skills need (not made here)

- **navigation** (`tools/zed-tools.md`): a pointer that Zed's Python
  diagnostics come from basedpyright and ruff by default
  (`linting/core/zed.md`); and in `tools/type-checkers.md`, a pointer to
  linting for the lasting setting behind `--follow-untyped-imports`.
- **deployment** (`gitlab/python.md`): a pre-commit job using
  `pre-commit/ci.md`'s commands needs enough git history for
  `--from-ref` (a shallow clone failed); nothing in deployment sets the
  depth yet.
- **packaging**: dev-group advice for `pre-commit-hooks`,
  `pyright[nodejs]`, and a `.python-version` (uv chose Python 3.14 in
  the lab when only `requires-python = ">=3.12"` was set, which changes
  mypy's target).
- **git**: the `core.hooksPath` case (calling `pre-commit run` from the
  existing hook) and `.git-blame-ignore-revs` for formatting commits.
- **roadmap**: decision L7 now reads `uv run --frozen`, not `--no-sync`,
  for hook entries.
