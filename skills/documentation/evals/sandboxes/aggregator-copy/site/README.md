# Payments team docs

Builds the team's docs site from each repository's `docs` folder.

```powershell
uv run --no-sync python collect_docs.py
uv run --no-sync mkdocs build --strict
```

The repositories must be checked out next to this one.
