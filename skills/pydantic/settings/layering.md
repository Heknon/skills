# Layering: which value lives where

One settings class per service, read once, from layers that each have
one job. deployment owns how a value reaches the process (CI
variables, ConfigMaps, Secrets); this file starts where the variable or
file reaches the process.

| Layer | Holds | Who writes it |
| --- | --- | --- |
| field defaults in code | safe values for local development; never secrets | developers, reviewed |
| `.env.example` (committed) | every key, harmless values, a comment each | developers, reviewed |
| `.env` (not committed) | one developer's own values | that developer |
| environment variables | the deployment's values for this environment | the deployment (deployment skill) |
| secrets directory | credentials, one file each | the platform (a mounted Secret) |
| `Settings(...)` arguments | tests only | tests |

In the default order the environment beats `.env`, which beats the
secrets directory (`settings/sources.md`). A service that must let
mounted secrets win over stray variables changes the order, and says so
in a comment where it does: the who-set-the-port confusion comes from an
order nobody wrote down.

## One class, not one per environment

Differences between environments are values, not classes: an
`environment: Literal["dev", "test", "prod"]` field read from
`APP_ENVIRONMENT`, and the deployment setting the variables for each.
A second class per environment duplicates fields and drifts.

A constant that differs by environment is a setting; one that does not
is a constant in code (where it goes: the architecture skill).

## The recipe

`recipes/settings/` is a complete, tested layering:

- `src/app/config.py`: `Settings` with `env_prefix="APP_"`, a nested
  `db` group (`APP_DB__HOST`), a top-level secret `db_password`
  (`secrets/app_db_password`), paths anchored to the project folder,
  `dotenv_filtering="match_prefix"`, and `get_settings()` cached with
  `lru_cache`.
- `.env.example`: every key.
- `tests/test_config.py`: defaults, environment over `.env`, init over
  environment, a typo caught, the secret masked; each test isolated
  from the developer's `.env` (`settings/testing.md`).
- `trace_settings.py`: which source set each value.

## Files as a layer

pydantic-settings can also read TOML, YAML, JSON and `pyproject.toml`
(`settings/sources.md` shows adding `TomlConfigSettingsSource`). Add one
only when the team already layers settings with a file, and put it
below the environment so the deployment can still override it.

## Changing a setting: the checklist

1. The field, with a type and a safe default (or none, if it must be
   provided).
2. `.env.example` updated with the key and a comment.
3. The variable name from `settings/env.md`, told to whoever sets it
   (deployment).
4. A test that shows the value arriving (`settings/testing.md`).
5. Where it is documented as a surface of the service: the
   documentation skill.
