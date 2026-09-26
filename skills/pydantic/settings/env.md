# Which variable a field reads

## The rule (*lab*, pydantic-settings 2.15.0)

| Field declared as | Reads |
| --- | --- |
| `port: int` with `env_prefix="APP_"` | `APP_PORT` (any case: `case_sensitive=False` by default) |
| `db: Db` with `env_nested_delimiter="__"` | `APP_DB__HOST` for `db.host`, and `APP_DB` as JSON for the whole object |
| `db: Db` without a delimiter | `APP_DB` as JSON only: `'{"user": "json-user"}'` |
| `hosts: list[str]` | `APP_HOSTS` as JSON: `'["a", "b"]'`; *lab:* `a,b` failed with `SettingsError: error parsing value for field "hosts" from source "EnvSettingsSource"` |
| `db_url: str = Field(validation_alias="DATABASE_URL")` | `DATABASE_URL`: the prefix is **not** added to an alias; `APP_DB_URL` is ignored |
| same, with `env_prefix_target="all"` (2.13+) | `APP_DATABASE_URL` |
| `level: str = Field(validation_alias=AliasChoices("APP_LEVEL", "LOG_LEVEL"))` | either name |
| `PORT: int` with `case_sensitive=True` | exactly `APP_PORT`; a field `port` then reads `APP_port` only (*lab:* `APP_PORT` was ignored) |

Every value arrives as a string and is converted in lax mode
(`typing/strict-and-lax.md`). An empty value is a value: *lab:*
`APP_PORT=` gave `int_parsing` with input `''`; `env_ignore_empty=True`
treats it as unset. `env_parse_none_str="null"` turns that text into
`None` (*lab*).

## Case

With the default `case_sensitive=False`, names are compared in lower
case. On Linux two variables can differ only in case; *lab:* with both
`APP_PORT=8500` and `app_port=1111` set, the result was `1111`. Which
one wins then depends on the order of the environment; never rely on
it.

On Windows, environment variable names are case-insensitive, so
`APP_PORT` and `app_port` are the same variable (*not run on Windows*).

## PowerShell

```
$env:APP_PORT = "9001"                   # this session only
uv run --no-sync python -m app.main
Remove-Item Env:APP_PORT                 # unset it again
Get-ChildItem Env:APP_*                  # what is set now (never for secrets)
```

A variable set with `$env:` lives only in that PowerShell session and
its children: a new terminal, or Zed's agent terminal, does not see it.
A value set in System Properties or with `setx` reaches only new
processes (*not run on Windows*). When a value "does not change", a
stale variable in the current session is a common cause: the trace
script shows it (`settings/trace.md`).

POSIX equivalents: `export APP_PORT=9001`, `unset APP_PORT`,
`env | grep ^APP_` (again, never for secrets).

## Choosing names

- One prefix per service, ending in `_`: `BILLING_`.
- Nested models with `env_nested_delimiter="__"` for groups
  (`APP_DB__HOST`), except secrets, which stay top-level fields so one
  file in the secrets directory can hold each (`settings/secrets.md`).
- An alias only when the name is fixed by something else (a platform's
  `DATABASE_URL`); remember it ignores the prefix.

The documentation skill lists settings as a surface of a service; this
file's table is the rule for naming each field's variable.
