# Template: repository README

The README is the front door. It says what the repository is and how to
start, then points to the docs. Keep it under one screen; everything else
goes in `docs\`.

````markdown
# <name, as in pyproject.toml>

<One sentence: what it does, for whom.>

## Install

```powershell
uv sync --offline
```

## Run

```powershell
uv run --no-sync <the command, from [project.scripts] or __main__>
```

## Test

```powershell
uv run --no-sync pytest -q
```

## Docs

<Link to docs/index.md, and to this component's page on the combined site.>

## Owner

<Team, from CODEOWNERS or the team page; or ask.>
````

Every command in it was run, or is marked `not run`.
