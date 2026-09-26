# Settings in tests, and settings at import time

## Built at import: the trap

```python
# config.py
class Settings(BaseSettings):
    db_password: SecretStr          # required
    port: int = 8000

settings = Settings()               # runs on import
```

*lab (2.15.0):* importing that module with `APP_DB_PASSWORD` unset
failed with `ValidationError ... db_password  Field required`: every
module, test and tool that imports it fails, before any test can set a
variable. And once built, the values are fixed: a test that sets
`APP_PORT` afterwards changes nothing. This is not pytest's fault.

Build on first use and cache it:

```python
from functools import lru_cache

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Code calls `get_settings()` where it needs a value. Tests clear the
cache so each one builds fresh settings.

## Isolating a test (`recipes/settings/tests/test_config.py`)

```python
@pytest.fixture(autouse=True)
def fresh_settings(monkeypatch):
    for name in list(os.environ):
        if name.upper().startswith("APP_"):
            monkeypatch.delenv(name)                               # no stray variables
    monkeypatch.setitem(Settings.model_config, "env_file", None)  # no developer .env
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
```

*lab:* with a developer `.env` holding `APP_PORT=1234` in the project,
the recipe's six tests passed; without the `env_file` line,
`test_defaults` failed with `assert (1234, 'dev', 'devbox') == (8000,
'dev', 'localhost')`. The sources read `model_config` each time the
class is built, so patching it for the test works; `monkeypatch` puts it
back afterwards. (How `monkeypatch` and fixtures work is the pytest
skill's ground.)

In a single test:

| Need | Write | *lab* |
| --- | --- | --- |
| a variable | `monkeypatch.setenv("APP_PORT", "9001")`, then `get_settings()` | `9001`; nested `APP_DB__HOST` merged with defaults |
| an explicit value | `Settings(port=7000)` | beats the environment |
| no `.env` at all | `Settings(_env_file=None)` | the file is skipped |
| a specific `.env` | `Settings(_env_file=tmp_path / ".env")` | read from there |
| a specific secrets folder | `Settings(_secrets_dir=tmp_path)` | a file `app_port` there set `port` |

The underscore arguments (`_env_file`, `_env_file_encoding`,
`_secrets_dir`, `_case_sensitive`, `_env_prefix`, ...) are
pydantic-settings' per-call overrides of `model_config`; they are not
fields.

## FastAPI

Where settings are injected with `Depends(get_settings)`, a test can
replace them through `app.dependency_overrides`; the mechanics are the
api skill's ground.
