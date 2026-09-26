# Surfaces in Python code

**What it decides:** what a reader can touch without reading the code,
so an Audit knows what must be documented.

A **surface** is a command, an option, a setting, an address or a
function that someone outside the code uses. Every surface needs a place
in the docs; nothing else does.

Search with the editor's `grep` (regular expressions, Rust syntax). Each
pattern over-reports: read every hit and keep only real surfaces. Search
tips and what search misses are in the navigation skill.

| Surface | Where it is | Pattern |
| --- | --- | --- |
| installed command | `pyproject.toml`, `[project.scripts]` | read the table |
| module run as a program | `if __name__ == "__main__":` | P1 |
| command-line option, argparse | `add_argument(` calls | P2 |
| command-line option, click or typer | decorators and parameters | P3 |
| environment variable | `os.environ`, `os.getenv` | P4 |
| settings class | pydantic `BaseSettings` fields, each read from the environment | P5 |
| configuration file key | the code that loads the file, then each key it reads | P6 |
| HTTP route | framework decorators or URL lists | P7 |
| public Python API | `__all__`, names imported in a package's `__init__.py` | P8 |
| message, queue, topic | producer and consumer calls with a literal name | P9 |
| scheduled job | task decorators, cron files | P10 |

The patterns, to type into `grep` as they are:

```
P1   __name__ == .__main__.
P2   add_argument\(
P3   @click\.(command|group|option|argument)|typer\.(Option|Argument)|@\w+\.command
P4   os\.environ|os\.getenv|environ\.get
P5   BaseSettings
P6   yaml\.safe_load|tomllib\.load|json\.load|configparser
P7   @\w+\.(get|post|put|patch|delete|route)\(|re_path\(|\bpath\(
P8   __all__
P9   publish\(|subscribe\(|send_message\(|topic=
P10  @shared_task|@\w+\.task\b|crontab
```

For a settings class, take each variable's name from the pydantic
skill's `settings/env.md`: a prefix is added to a field, not to an alias.

## For each surface, record

- its exact name, as the code spells it;
- where it is defined, `path:line`;
- its default, read from that line, or `none`;
- whether a page, the README or a docstring states what it does:
  **documented**, **mentioned** (the name appears with no explanation),
  or **undocumented**.

A surface that must stay undocumented (internal, experimental,
deprecated) is left out only when a record says so: a comment at its
definition, the team's docs, or the person asking.
