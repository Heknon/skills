# Layered settings, their tests, and the trace script

A complete settings module for one service, with tests, and a script
that shows which source set each value. Copy what you need.

| File | What it is |
| --- | --- |
| `src/app/config.py` | `Settings` (prefix `APP_`, nested `db` group, top-level secret `db_password`, paths anchored to the project folder, `dotenv_filtering="match_prefix"`) and `get_settings()` cached with `lru_cache` |
| `.env.example` | every key with a harmless value; copy to `.env` for local work |
| `tests/test_config.py` | six tests, each isolated from the developer's `.env` and stray `APP_` variables |
| `trace_settings.py` | per field, the winning source and every other source that set it; secrets masked |
| `pyproject.toml` | a uv project to run the tests (pydantic 2.13+, pydantic-settings 2.14+) |

## Use it

1. Copy `src/app/config.py` to `src/<package>/config.py`. Change the
   fields, the prefix, and `parents[2]` if the file sits at another
   depth below the project folder.
2. On pydantic-settings older than 2.14, replace
   `dotenv_filtering="match_prefix"` with `extra="ignore"`: the older
   release ignores the key without a warning (*lab*, 2.13.1).
3. Copy `.env.example` and the tests; keep the `fresh_settings` fixture.
4. Call `get_settings()` where a value is needed; never build
   `Settings()` at module level (`settings/testing.md`).

## Run it (PowerShell or POSIX)

```
cd recipes/settings
uv sync
uv run pytest                          # 6 passed
```

*lab:* 6 passed on pydantic-settings 2.15.0 and 2.14.1 (pydantic
2.13.5), also with a developer `.env` (`APP_PORT=1234`) present; on
2.13.1, `test_dotenv_file` failed with `extra_forbidden` on
`compose_project_name`, as step 2 says.

## The trace script

Run from the folder the service is started from, with the variables it
is started with:

```
$env:APP_PORT = "9100"
$env:PYTHONPATH = "src"; uv run --no-sync python trace_settings.py app.config:Settings; Remove-Item Env:PYTHONPATH
APP_PORT=9100 PYTHONPATH=src uv run --no-sync python trace_settings.py app.config:Settings   # POSIX
```

*lab* (a `.env` with `APP_PORT=1234` and `APP_DB__HOST=devbox`, and
`secrets/app_db_password`):

```
per field (the first line wins):
  environment = 'dev'   <- default
  port = '9100'   <- EnvSettingsSource
      also set by DotEnvSettingsSource: '1234'
      also set by default: 8000
  log_level = 'info'   <- default
  db.host = 'devbox'   <- DotEnvSettingsSource
      also set by default: 'localhost'
  db.name = 'app'   <- default
  db.port = 5432   <- default
  db.user = 'app'   <- default
  db_password = <secret, 16 chars>   <- SecretsSettingsSource
      also set by default: <secret, 0 chars>

building the class:
  ok
```

It also ran on pydantic-settings 2.12.0, and on classes with
`validation_alias`, `AliasChoices`, a custom source order, extra keys in
`.env` (listed, and the build failure shown without inputs) and nested
secrets. Its masking is by type (`SecretStr`, `SecretBytes`) and by
name (password, secret, token, key, credential, dsn, url, anywhere in
the dotted path); a secret in a field with another name and type `str`
would be shown: type it `SecretStr`.
