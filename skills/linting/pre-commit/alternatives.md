# prek and plain git hooks: recognise, do not teach

**What it decides:** what you are looking at when a repository does not
use pre-commit itself. Verified on prek 0.5.3 (the version on the
index); the team has not chosen it, so this skill does not teach it.

## prek

A reimplementation of pre-commit in Rust that reads the same
`.pre-commit-config.yaml`. Signs: a `prek` in the dev group or on
`PATH`, `prek install` in a README, hook scripts that mention prek.

What the lab saw:

- `prek run --all-files` ran the same local hooks with the same output
  format (`ruff check....Passed`).
- Its commands differ: `install`, `prepare-hooks`, `run`, `list`,
  `validate-config`, `update`, `cache`, and `--skip <HOOK|PROJECT>` on
  the command line.
- **Nested configs are live in prek.** In a uv workspace it ran
  `services/api/.pre-commit-config.yaml` as a project of its own, from
  inside `services/api`, next to the root config; pre-commit ignores
  that file on commit (`pre-commit/monorepo.md`).

If a repository uses prek, say so, run `prek --help` and
`prek <command> --help` for the facts, and do not assume pre-commit's
behaviour where it matters (nested configs, skipping, installing).

## Plain git hooks

Scripts in `.git/hooks` or in the folder `core.hooksPath` names, with
no pre-commit behind them. Read them before changing anything; they may
be required by another team. To add pre-commit's checks without
replacing them, call `uv run --frozen pre-commit run` from the existing
script (`pre-commit/install.md`).
