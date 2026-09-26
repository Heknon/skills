# Glossary

One sentence per term. Use these words and no synonyms.

| Term | Meaning |
| --- | --- |
| checker | One of the tools this skill runs: ruff (linter and formatter), mypy, pyright or basedpyright. |
| finding | One line a checker reports: a file, a position, a code or rule name, and a message. |
| code | The identifier of a finding: a ruff rule code (`F401`), a mypy error code (`arg-type`), or a pyright rule (`reportArgumentType`). |
| rule | A ruff check with a code and a name, such as `F401` `unused-import`; `ruff rule <CODE>` explains it offline. |
| linter group | The prefix that groups ruff rules by origin, such as `F` (Pyflakes) or `B` (flake8-bugbear); `ruff linter` lists them. |
| default rules | The rules ruff enables when the config has no `select`; they changed between versions (59 on 0.15.8, 413 on 0.16.9). |
| fix | A change ruff can apply for a finding; `[*]` marks one that `--fix` applies. |
| unsafe fix | A fix ruff applies only with `--unsafe-fixes`, because it may change behaviour or drop comments. |
| suppression | A comment that silences one finding on one line: `# noqa: F401`, `# type: ignore[arg-type]`, `# pyright: ignore[reportArgumentType]`. |
| blanket suppression | A suppression without a code (`# noqa`, `# type: ignore`, `# pyright: ignore`), or for a whole file (`# ruff: noqa`). |
| config file | The one file a checker read its settings from; each tool can print it. |
| override | A per-module (mypy) or per-path (pyright, ruff `per-file-ignores`) setting that differs from the project default. |
| strict mode | mypy's `strict = true` or pyright's `typeCheckingMode = "strict"`: a bundle of stricter checks. |
| stub | A `.pyi` file that gives types to code that has none. |
| `py.typed` | A marker file in an installed package that says its own annotations are to be used. |
| plugin | Code a checker loads to understand a library, such as `pydantic.mypy`. |
| baseline | The findings accepted at a point in time so that only new ones fail, kept as a ratchet (mypy overrides) or comments (`ruff check --add-noqa`). |
| ratchet | A written list of modules still exempt from a stricter setting, which only ever shrinks. |
| language server | A checker run by the editor to fill Zed's diagnostics panel. |
| hook | A check pre-commit runs from `.pre-commit-config.yaml`, named by its `id`. |
| hook type | The git hook pre-commit is installed as: `pre-commit`, `commit-msg`, `pre-push` and others; one script per type in `.git/hooks`. |
| stage | The hook type at which a hook runs, set by `stages`; `manual` runs only when asked. |
| local hook | A hook under `repo: local`, defined in the project's own config; nothing is fetched. |
| hook repository | A git repository with a `.pre-commit-hooks.yaml`, named by `repo:` and `rev:`; fetched on first use. |
| hook environment | The virtualenv pre-commit builds for a `language: python` hook, kept under `PRE_COMMIT_HOME`. |
| `PRE_COMMIT_HOME` | pre-commit's cache of hook repositories and environments; default `~/.cache/pre-commit`. |
| lock's version | The version of a tool pinned in `uv.lock`, which CI installs with `uv sync --locked`. |
