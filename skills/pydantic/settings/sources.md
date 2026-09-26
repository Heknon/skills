# Sources and their order

**Verdict you produce** for a settings change: the settings class, the
variable name each changed field reads (`settings/env.md`), and a probe
or test that shows the value arriving.

```
class:    <module>:<Class>, pydantic-settings <version>
fields:   <field> <- <VARIABLE_NAME> | .env | secrets/<file> | default
probe:    <command> -> <printed values, secrets masked>
```

## The default order

A `BaseSettings` class reads every source and merges them; for each
value, the highest source that sets it wins:

1. arguments to the constructor, `Settings(port=1)`
2. environment variables
3. the `.env` file(s) in `env_file`
4. the secrets directory `secrets_dir`
5. the field defaults

*lab (2.15.0, and the same on 2.8.1 and 2.12.0):* with `a` to `e` set
in progressively fewer sources, the result was `{'a': 'init', 'b':
'env', 'c': 'dotenv', 'd': 'secret', 'e': 'default'}`. A secrets file
loses to `.env`: mounted secrets do not override a developer's `.env`
unless the order is changed.

Nested values merge across sources field by field: *lab:*
`APP_DB__USER` from `.env` and `APP_DB__NAME` from the environment
together gave `db={'user': 'dotenv-user', 'name': 'env-db'}`.

## Changing the order, adding or removing a source

Override the class method; the tuple is the order, highest first:

```python
class Settings(BaseSettings):
    ...
    @classmethod
    def settings_customise_sources(
        cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings
    ):
        return init_settings, file_secret_settings, env_settings, dotenv_settings
```

*lab:* with that order, `secrets/app_port` (9000) beat `APP_PORT` in
the environment (8500) and in `.env` (7000). Leaving a source out of
the tuple switches it off.

A file source is added the same way; its key in `model_config` alone
does nothing:

```python
from pydantic_settings import TomlConfigSettingsSource

    @classmethod
    def settings_customise_sources(cls, settings_cls, init_settings, env_settings,
                                   dotenv_settings, file_secret_settings):
        return (init_settings, env_settings, dotenv_settings,
                TomlConfigSettingsSource(settings_cls), file_secret_settings)
```

*lab:* with `toml_file="config.toml"` and that tuple, TOML values filled
what the environment did not set. With `toml_file` set but no source
added, 2.15.0 warns: `Config key toml_file is set in model_config but
will be ignored because no TomlConfigSettingsSource source is
configured.` JSON, YAML, `pyproject.toml`, the command line and cloud
secret stores have sources too; only add one when the team layers
settings with files (`settings/layering.md`), and cloud stores cannot be
reached air gapped.

## Seeing what each source gave

The safe way is the trace script (`settings/trace.md`), which masks
secrets. pydantic-settings 2.15 also logs every source's values when
`PYDANTIC_SETTINGS_DEBUG=1` and the `pydantic_settings` logger is at
`DEBUG`; *lab:* it printed `EnvSettingsSource: {'password': 'hunter2'}`
in clear. Do not use it where the output is kept or shared.

## Where to go next

| Part | File |
| --- | --- |
| variable names, prefixes, case, nesting, PowerShell | `settings/env.md` |
| `.env` files: path, encoding, extra keys | `settings/dotenv.md` |
| secrets directories and `SecretStr` | `settings/secrets.md` |
| which layer holds which value | `settings/layering.md` |
| where a value came from | `settings/trace.md` |
| settings in tests, settings at import time | `settings/testing.md` |
