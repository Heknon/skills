# .pre-commit-config.yaml

**What it decides:** what each key does, which files and stage each hook
covers, and the YAML traps. Keys read in pre-commit 4.6.2's
`clientlib.py`; behaviour run in the lab.

## A local hook, key by key

```yaml
default_install_hook_types: [pre-commit, commit-msg]   # what `pre-commit install` installs
default_stages: [pre-commit]                           # stage for hooks without `stages`
repos:
  - repo: local                                        # defined here; nothing fetched
    hooks:
      - id: ruff-check                                 # the name for SKIP and `pre-commit run <id>`
        name: ruff check                               # the label in the output
        entry: uv run --frozen ruff check --force-exclude
        language: system                               # run entry as a command
        types_or: [python, pyi]                        # only files with one of these tags
        require_serial: true                           # one process with all files
      - id: mypy
        name: mypy
        entry: uv run --frozen mypy src
        language: system
        types_or: [python, pyi]
        pass_filenames: false                          # run once, without file names
```

| Hook key | Does |
| --- | --- |
| `entry` | the command; split with Python's `shlex.split`, so quotes group words and **a backslash is an escape**: `scripts\check.py` became `scriptscheck.py`. Use `/` in paths, on Windows too |
| `args` | extra arguments, appended after `entry` |
| `language` | `system` runs `entry` as found on `PATH` (4.6.2 files it under the new name `unsupported`); `python` builds a virtualenv (`pre-commit/offline.md`); `pygrep`, `fail` and others exist |
| `files`, `exclude` | **regular expressions** on the path from the repository root, such as `^services/api/`; `services/api/*` got `The 'files' field in hook 'a' is a regex, not a glob` |
| `types`, `types_or`, `exclude_types` | file tags from the `identify` package (`identify-cli <file>` prints them: `python`, `pyi`, `text`, `toml`, `yaml`, `file`, ...); `types` needs all, `types_or` any |
| `stages` | the stages the hook runs at; default `default_stages`, which defaults to all stages |
| `pass_filenames` | `false` for tools that check a whole project, like mypy |
| `require_serial` | `true` to run one process; otherwise files are split into batches run in parallel (*lab*: two `echo` runs of 4 files each on a 4-CPU machine). A very long file list is split anyway to fit the command line |
| `always_run` | run even when no file matches |
| `additional_dependencies` | extra packages for `language: python` hooks |
| `verbose` | print the output even when the hook passes |
| `fail_fast` | stop the run after this hook fails (also a top-level key) |

Top-level keys: `repos`, `default_install_hook_types`,
`default_language_version`, `default_stages`, `files`, `exclude`,
`fail_fast`, `minimum_pre_commit_version`, and `ci` (for pre-commit.ci,
not used here).

## Stages

Stage names in 4.6.2: `pre-commit`, `pre-merge-commit`, `pre-push`,
`commit-msg`, `prepare-commit-msg`, `post-checkout`, `post-commit`,
`post-merge`, `post-rewrite`, `pre-rebase`, and `manual` (only when run
with `--hook-stage manual`). The old names `commit` and `push` still
work with `[WARNING] hook id a uses deprecated stage names (push)`;
`pre-commit migrate-config` rewrites them.

**Set `default_stages: [pre-commit]` whenever any hook has another
stage.** Without it, hooks with no `stages` run at every installed
stage. *Lab:* with `commit-msg` installed, the ruff and mypy hooks ran
again at the commit-msg stage, and a hook without `types` received
`.git/COMMIT_EDITMSG` as its file.

## YAML traps, each seen in the lab

| Trap | What happened |
| --- | --- |
| an unquoted `entry:` containing ` #` | YAML cut the entry at the `#`; `validate-config` passed; the run died with `An unexpected error has occurred: ValueError: No closing quotation`, exit 3. Put logic in a script file, or quote the whole value |
| a misspelt hook key (`stage:` for `stages:`) | `validate-config` said nothing; `run` printed `[WARNING] Unexpected key(s) present on local => a: stage`, and the hook ran at every stage (it ran at commit-msg) |
| a misspelt top-level key (`default_stage:`) | `[WARNING] Unexpected key(s) present at root: default_stage`, exit 0 |
| a misspelt language (`sytem`) | `validate-config` failed: ``Expected one of conda, ..., unsupported, unsupported_script but got: 'sytem'`` |
| bad indentation | `while parsing a block mapping ... did not find expected key`, with the line |
| a glob in `files:` | the regex warning above |

## Validate after every edit

```
uv run --frozen pre-commit validate-config
uv run --frozen pre-commit run --all-files
```

`validate-config` catches schema and YAML errors, not misspelt hook
keys and not a broken `entry`; only the run shows those, so read its
`[WARNING]` lines too. Run both, and stage the config first:
`pre-commit run` without `--all-files` refused with `[ERROR] Your
pre-commit configuration is unstaged.`
