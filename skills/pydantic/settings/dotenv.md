# `.env` files

## The path is relative to the working directory

`env_file=".env"` is resolved from the folder the process was started
in, not from the code's folder, and a missing file is skipped with no
error. *lab (2.15.0):*

```
cd services/billing; uv run --no-sync python -m billing.main
billing listening on port 7001, currency GBP        <- .env read
cd <repository root>; uv run --project services/billing python -m billing.main
billing listening on port 8000, currency EUR        <- defaults, silently
```

Anchor the path to the file that defines the settings:

```python
from pathlib import Path

# src/billing/config.py -> parents[2] is the project folder
SERVICE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BILLING_", env_file=SERVICE_DIR / ".env")
```

*lab:* it then read the file from the root, from the service folder and
from `/tmp`, and a variable still beat it (`BILLING_PORT=9` gave 9).
With an editable install (`uv sync`) `__file__` is in `src/`; in a
wheel installed into site-packages the anchored path points there and
no `.env` is found, which is right for a deployed service: it gets its
values from the environment (deployment's ground).

## Several files

`env_file=(".env", ".env.local")`: later files win. *lab:* `.env`
`APP_PORT=7000`, `.env.local` `APP_PORT=7100` gave `7100`; keys only in
`.env` still arrived.

## Encoding

| File | *lab* result |
| --- | --- |
| UTF-8 | read |
| UTF-8 with a BOM | read |
| UTF-16 | `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0` when the class is built |
| UTF-16 with `env_file_encoding="utf-16"` | read |

Windows PowerShell 5.1 writes UTF-16 with `>` and `Out-File`, so
`"APP_PORT=1" > .env` makes a file that fails to load (*not run on
Windows*). Write it with an explicit encoding, or edit it in the
editor:

```
Set-Content -Path .env -Value "APP_PORT=8000" -Encoding utf8   # 5.1: UTF-8 with a BOM, which loads
```

## Syntax (python-dotenv, *lab*)

`APP_PORT=7000 # comment` gives `7000`; `APP_NAME="a b"` gives `a b`;
`APP_PORT=` gives the empty string (an `int_parsing` error unless
`env_ignore_empty=True`).

## Keys that match no field

`BaseSettings` defaults to `extra="forbid"`, and a `.env` key that
matches no field is an extra input, **with or without the prefix**.
*lab:*

```
extra_forbidden  ('compose_project_name',)   from COMPOSE_PROJECT_NAME=shop
extra_forbidden  ('pgadmin_default_email',)
```

Environment variables without the prefix are ignored; only the file is
checked this way. When the file is shared with other tools (docker
compose, pgAdmin), choose:

| Setting | Other tools' keys | A misspelt `APP_` key in `.env` | Version |
| --- | --- | --- | --- |
| `dotenv_filtering="match_prefix"` | ignored | still `extra_forbidden` (*lab:* `APP_DEBGU` gave `debgu`) | 2.14+ |
| `dotenv_filtering="only_existing"` | ignored | ignored | 2.14+ |
| `extra="ignore"` | ignored | ignored | all |
| `extra="allow"` | **kept on the settings object** (*lab:* `compose_project_name='shop'` in the dump) | kept | all |

Prefer `match_prefix` where installed; else `extra="ignore"`. Check the
version first: *lab:* on 2.13.1, `dotenv_filtering="match_prefix"` was
accepted with no warning and did nothing (the compose key still gave
`extra_forbidden`). Never `extra="allow"`, and never delete other
tools' keys from a shared file.

## Never commit `.env`

Commit a `.env.example` with every key and harmless values
(`recipes/settings/.env.example`); `.env` holds a developer's own
values and often secrets.
