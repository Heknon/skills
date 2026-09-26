# Worked example: a setting the deployment cannot change

Kinds: Trace, Settings. Outputs from a lab run on pydantic-settings
2.15.0, pydantic 2.13.5.

## The ask

> The worker runs 2 jobs at a time. The deployment sets
> WORKER_CONCURRENCY=8. Why is it ignored?

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WORKER_", env_file=".env", extra="ignore")

    queue: str = "default"
    concurrency: int = Field(1, validation_alias="CONCURRENCY")
    broker_password: SecretStr = SecretStr("")
```

`.env` holds `CONCURRENCY=2`, `WORKER_QUEUE=local` and a password.

## Steps

1. **Reproduce as deployed**: with `WORKER_CONCURRENCY=8` set,
   `Settings()` gave `concurrency=2`.
2. **Trace** (`settings/trace.md`): copied
   `recipes/settings/trace_settings.py` into the project and ran it with
   the deployment's variable:
   ```
   $env:WORKER_CONCURRENCY = "8"
   $env:PYTHONPATH = "src"; uv run --no-sync python trace_settings.py worker.config:Settings; Remove-Item Env:PYTHONPATH
   ```
   ```
   sources, highest priority first:
     1. InitSettingsSource
     2. EnvSettingsSource (process environment)
     3. DotEnvSettingsSource .../.env (found)
     4. SecretsSettingsSource (secrets_dir not set)

   per field (the first line wins):
     concurrency = '2'   <- DotEnvSettingsSource
         also set by default: 1
     broker_password = <secret, 7 chars>   <- DotEnvSettingsSource
   ```
   The environment source did not set `concurrency` at all, although
   `WORKER_CONCURRENCY` was set: the source is not reading that name.
3. **Which name does the field read?** (`settings/env.md`): a
   `validation_alias` is used as the variable name **without** the
   prefix. The field reads `CONCURRENCY` only; `WORKER_CONCURRENCY` is
   an unknown variable, and environment variables that match no field
   are ignored. The developer's `.env` happens to use `CONCURRENCY`, so
   it worked locally.
4. **Fix, keeping both names working**:
   `Field(1, validation_alias=AliasChoices("WORKER_CONCURRENCY",
   "CONCURRENCY"))`. Traced again:
   ```
   concurrency = '8'   <- EnvSettingsSource
       also set by DotEnvSettingsSource: '2'
       also set by default: 1
   ```
   Without the variable (local work), `Settings().concurrency` was `2`
   from `.env`, as before.

## The answer

```
## Result
concurrency has validation_alias="CONCURRENCY", and an alias is used
without env_prefix, so the field never read WORKER_CONCURRENCY; the 2
came from .env (CONCURRENCY=2). Changed it to
AliasChoices("WORKER_CONCURRENCY", "CONCURRENCY") in
src/worker/config.py. The deployment's value now wins; local .env files
keep working. Removing the alias instead would be simpler, but every
.env that uses CONCURRENCY would then be ignored (extra="ignore").

## Checked
- Before: trace showed concurrency = '2' <- DotEnvSettingsSource, no
  environment entry, with WORKER_CONCURRENCY=8 set.
- After: concurrency = '8' <- EnvSettingsSource, also set by .env '2'.
- Without the variable: Settings().concurrency == 2.
- pydantic-settings 2.15.0; broker_password shown only as its length.

## Not checked
- The running deployment: redeploy and read the worker's startup log or
  its concurrency metric.
```
