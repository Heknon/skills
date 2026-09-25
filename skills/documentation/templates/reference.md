# Template: reference

For someone looking one fact up. Complete, exact, in a fixed order, no
teaching. Generate it when a tool can: mkdocstrings for Python API
(`mkdocs/api-reference.md`), `--help` output for commands.

For settings or environment variables, a table, with every row read from
the code:

```markdown
# <Component> settings

<One sentence: where these are read, path:line of the loader.>

| Name | Default | Meaning |
| --- | --- | --- |
| `BILLING_TIMEOUT` | `30` | seconds to wait for the payment gateway |
```

For commands:

````markdown
# <command>

```
<output of `uv run --no-sync <command> --help`, pasted>
```
````

Sorted the way the code lists them, or alphabetically. No steps, no
opinions.
