# Trace where a value came from

**Verdict you produce:** the winning source, and every other source
that also set the value, with secrets masked.

```
field:    <field>  = <value, or <secret, N chars>>
winner:   <source> <file or variable>, because <its place in the order>
also:     <source>: <value>   (one line each, highest first)
order:    <the tuple settings_customise_sources returns, or "default">
run from: <working directory, and the variables set as the service is started>
```

Never edit `.env` again before this verdict: a higher source may be
winning.

## With the script

`recipes/settings/trace_settings.py` builds the class's own sources, in
its own order, calls each alone, and prints per field every source that
set it. It changes nothing and masks secrets (`SecretStr` fields, and
names containing password, secret, token, key, credential, dsn or url).

1. Copy it into the project folder (it is a probe; delete it after).
2. Start it the way the service is started: the same working directory,
   the same variables. If a script such as `run.ps1` sets variables,
   set them the same way first.
3. Run it with the class's import path:

```
$env:API_PORT = "8080"                        # as run.ps1 does
$env:PYTHONPATH = "src"; uv run --no-sync python trace_settings.py api.config:Settings; Remove-Item Env:PYTHONPATH
```

*lab* (the who-set-the-port case, pydantic-settings 2.15.0):

```
env_prefix: 'API_'  case_sensitive: False  nested_delimiter: None  extra: 'forbid'
sources, highest priority first:
  1. InitSettingsSource
  2. SecretsSettingsSource .../secrets (found)
  3. EnvSettingsSource (process environment)
  4. DotEnvSettingsSource .../.env (found)

per field (the first line wins):
  port = '9000'   <- SecretsSettingsSource
      also set by EnvSettingsSource: '8080'
      also set by DotEnvSettingsSource: '7000'
      also set by default: 8000
  log_level = 'debug'   <- DotEnvSettingsSource
      also set by default: 'info'
  db_password = <secret, 28 chars>   <- SecretsSettingsSource
```

Values are shown as the sources give them (strings) before conversion.
The script also prints `NOT FOUND` for an `env_file` or `secrets_dir`
that does not exist from this working directory (the `.env` ignored
case, `settings/dotenv.md`), keys that match no field (the
`extra_forbidden` case), and whether the class builds, with error types
but never inputs.

## By hand

When the script cannot run, answer the same questions in order:

1. **The order.** Does the class define `settings_customise_sources`?
   Its return tuple is the order; otherwise the default (init, env,
   `.env`, secrets, defaults).
2. **The name.** Which variable does the field read (`settings/env.md`)?
3. **Each source alone:**
   - init: is the class built with arguments (`Settings(port=...)`)?
   - environment: `Get-ChildItem Env:API_PORT` (POSIX `printenv
     API_PORT`) in the shell that starts the service, and in its start
     script;
   - `.env`: which file, resolved from which working directory; does it
     exist; which key;
   - secrets: which directory, does a file named like the variable
     exist (check its length, not its content).
4. The first source in the order that has it wins.

## Then

Say which change fixes it and leave the choice to the person when more
than one is reasonable (remove the stray file or variable, or change
the order). Changing the source order changes behaviour for every
field; never do it unasked.
