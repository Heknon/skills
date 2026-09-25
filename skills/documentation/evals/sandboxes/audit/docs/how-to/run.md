# How to run an ingest

1. Put the files in one folder.
2. Run `uv run --no-sync ingest --source <folder>`.

Rows are written in batches of 500. Set `INGEST_BATCH` to change it.
