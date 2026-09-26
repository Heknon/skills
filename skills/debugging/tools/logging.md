# Logging as a probe

**What it decides:** how to see the debug messages one module already
writes, for one run, without changing how the project logs. Designing
logs, levels in production and log backends are the observability
skill's.

## One logger, one run

Many modules already log at debug level (`log.debug(...)`) and nobody
sees it, because the root logger's level is `WARNING`. Turn on one
logger, by its name, from outside the code:

```powershell
uv run python -c "import logging; logging.basicConfig(level=logging.WARNING, format='%(name)s %(levelname)s %(message)s'); logging.getLogger('profiles.render').setLevel(logging.DEBUG); from profiles.serve import serve; serve(3)"
```

*lab (3.12.14, growing-cache sandbox):*

```
profiles.render DEBUG rendering user 0 for request 1
profiles.render DEBUG rendering user 1 for request 2
profiles.render DEBUG rendering user 2 for request 3
```

- The logger's name is usually the module's (`logging.getLogger(__name__)`):
  search the module for `getLogger` to be sure.
- `basicConfig` adds a handler to the root logger (*lab:* `[<StreamHandler
  <stderr> (NOTSET)>]`), which prints to stderr. Every other logger stays
  at `WARNING` (*lab:* `getEffectiveLevel()` was 10 for
  `profiles.render`, 30 for any other name), so only the chosen module's
  debug lines appear.
- **A level with no handler prints nothing.** *lab:* setting
  `profiles.render` to `DEBUG` without `basicConfig` printed no debug
  lines: the fallback handler only passes `WARNING` and above.
- If the program configures logging itself when it starts, it may
  replace this setup; then set the level after its setup runs, in a
  probe line marked `# DBG`, and remove it after.

## Never

- Never raise the whole application to `DEBUG` to find one value; the
  line you need drowns.
- Never commit a changed log level, handler or format as part of a fix.
- Never log a secret to see it.
