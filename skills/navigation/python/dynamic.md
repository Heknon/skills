# Dynamic Python: uses that do not spell the name

**What it decides:** how a function or class is reached when no line
calls it by name, and how to find that place.

## Registration by decorator

A decorator can store the function in a table, and other code calls it
from the table.

```python
HANDLERS = {}

def handler(kind):
    def register(fn):
        HANDLERS[kind] = fn
        return fn
    return register

@handler("refund")
def handle_refund(event): ...

HANDLERS[event["kind"]](event)   # the only call, and it names neither
```

To find it:
1. Read the line above the definition. A decorator is the first suspect.
2. Locate the decorator (`core/locate.md`) and read it. Find the table it
   writes into.
3. Search for reads of that table: `HANDLERS\[`, `HANDLERS.get(`.
4. Find where the key (`"refund"`) comes from at the call: the event, a
   route, a setting.

Frameworks do the same: `@app.get`, `@router.post`, `@celery.task`,
`@click.command`, `@pytest.fixture`, `@receiver` (Django signals),
`@register.filter` (Django templates), `@hookimpl` (pluggy).

## Names as strings

| Form | Search for |
| --- | --- |
| `getattr(obj, "save")`, `getattr(obj, name)` | `getattr\(` near the object; the name may be built from a variable |
| `importlib.import_module("app.jobs." + kind)` | `import_module\(`, `__import__\(`, then the string parts |
| dotted paths in settings: `"app.jobs.cleanup:run"`, `"app.jobs.cleanup.run"` | the module path in quotes, in `.py`, `.toml`, `.cfg`, `.ini`, `.yaml`, `.json` |
| Django: `INSTALLED_APPS`, `MIDDLEWARE`, `ROOT_URLCONF`, `urls.py` | dotted paths in `settings*.py` and `urls.py` |
| Celery task names, `send_task("name")` | the task's `name=` or its module path |
| `logging.config.dictConfig` | handler and filter class paths in the config |

## Classes chosen at runtime

- **Subclass registries**: `__init_subclass__` or a metaclass adds each
  subclass to a list; code loops over the list. Search for
  `__init_subclass__`, `metaclass=`, and reads of the registry.
- **Overrides**: `base.process()` runs whichever subclass the object is.
  Find every `def process` in subclasses of the base.
- **Dependency injection**: a container maps an interface to a class
  (`container.register(Repo, SqlRepo)`, `providers.Factory(...)`). Search
  for the class name in container or settings modules.

## Called by syntax

`__call__` (calling an instance), `__enter__`/`__exit__` (`with`),
`__iter__`/`__next__` (`for`), `__getitem__` (`[]`), `__eq__`, `__hash__`,
`__getattr__` (a missing attribute). Module-level `def __getattr__(name)`
serves names that are not defined in the module at all.

## pytest fixtures

A test receives a fixture by naming a parameter the same as the fixture.
To find where `db_session` in `def test_x(db_session)` comes from, look
for `def db_session` under `@pytest.fixture` in the same file, then in
`conftest.py` in the same folder, then in every parent folder's
`conftest.py` up to the root, then in plugins listed in `conftest.py` as
`pytest_plugins = [...]`. The nearest one wins.
