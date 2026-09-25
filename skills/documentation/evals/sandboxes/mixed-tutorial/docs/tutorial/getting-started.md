# Getting started

This tutorial gets Tracker running on your machine.

We built Tracker on SQLite rather than a server database. Tracker was
written in 2024 when the team needed something small, and there were
long discussions about which database to use, so the design is worth
understanding before you start: every request opens the file, and the
file lives next to where you start the server unless you change it.

## Configuration

Tracker reads these environment variables. You can set any of them
before starting.

| Variable | Default | Meaning |
| --- | --- | --- |
| `TRACKER_PORT` | `8080` | port the server listens on |
| `TRACKER_HOST` | `127.0.0.1` | address the server listens on |
| `TRACKER_DB` | `tracker.sqlite3` | path of the SQLite database file |
| `TRACKER_LOG_LEVEL` | `INFO` | logging level |
| `TRACKER_PAGE_SIZE` | `50` | items per page in lists |

## 1. Install

```powershell
uv sync --offline
```

## 2. Create the database

```powershell
uv run --no-sync tracker --init-db
```

## 3. Start the server

```powershell
uv run --no-sync tracker
```

Open http://127.0.0.1:8080 and you see `ok`.
