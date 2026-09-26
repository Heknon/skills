# Secrets

## A secrets directory

`secrets_dir="secrets"` (or a mounted path such as the one a
Kubernetes Secret volume gives; where it is mounted is deployment's
ground) makes each file a value: the file name is the variable name,
the content the value.

*lab (2.15.0)*, `env_prefix="APP_"`:

| File | Sets |
| --- | --- |
| `secrets/app_password` containing `s3cret\n` | `password = 's3cret'`: a trailing newline is stripped |
| `secrets/APP_TOKEN` | `token`: file names match in any case unless `case_sensitive=True` |
| `secrets/app_db__password` for a nested `db.password` | **nothing**: the plain secrets source does not split on `env_nested_delimiter` |
| `secrets/app_db` containing `{"password": "pw-json"}` | `db.password`: a nested model takes JSON |

The directory is relative to the working directory like `env_file`
(`settings/dotenv.md`). A missing directory warns on every build:
*lab:* `UserWarning: directory "/nonexistent/secrets" does not exist`.
The recipe sets it only when it exists:

```python
SECRETS_DIR = PROJECT_DIR / "secrets"
...
secrets_dir=SECRETS_DIR if SECRETS_DIR.is_dir() else None,
```

In the default order the secrets directory is **below** environment
variables and `.env` (`settings/sources.md`).

## Nested secrets, one file per value (2.12+)

`NestedSecretsSettingsSource` splits file names on a delimiter:

```python
from pydantic_settings import NestedSecretsSettingsSource

    @classmethod
    def settings_customise_sources(cls, settings_cls, init_settings, env_settings,
                                   dotenv_settings, file_secret_settings):
        return (init_settings, env_settings, dotenv_settings,
                NestedSecretsSettingsSource(file_secret_settings,
                                            secrets_nested_delimiter="__",
                                            secrets_dir_missing="ok"))
```

*lab:* `secrets/app_db__password` then set `db.password`, and a missing
directory gave no warning. The simpler choice, used by the recipe: keep
each secret a top-level field (`db_password`), which works on every
version.

## `SecretStr` and never showing a value

Type every secret field `SecretStr` (or `SecretBytes`): `repr`, `str`,
`model_dump()` and `model_dump_json()` show `'**********'` (*lab*).
The value comes out only through `.get_secret_value()`.

To check a secret without showing it:

```python
s = get_settings()
print("db_password set:", bool(s.db_password.get_secret_value()),
      "length:", len(s.db_password.get_secret_value()))
```

Never:

- print `settings`, `model_dump()` of it, or `os.environ` into a log or
  an answer when a field is a plain `str` holding a secret;
- enable `PYDANTIC_SETTINGS_DEBUG` where output is kept (it prints raw
  values, `settings/sources.md`);
- read a secret file with `Get-Content` or `cat` to "check it"; check
  its length (`(Get-Item secrets\app_db_password).Length`, *not run on
  Windows*; POSIX `wc -c secrets/app_db_password`).

A `ValidationError` includes the rejected input in its text; for a
secret that fails validation, `hide_input_in_errors=True` in the
model's config keeps it out (*lab*, `core/read-error.md`). The trace
script prints error types and locations without inputs.
