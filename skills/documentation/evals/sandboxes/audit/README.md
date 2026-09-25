# ingest

Loads the partners' CSV files into the reporting database.

## Run

```powershell
uv run --no-sync ingest --source D:\drops\partners
```

Add `--dry-run` to check the files without writing anything.

Rows are written in batches of 500.
