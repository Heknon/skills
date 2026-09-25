# What search misses

**What it decides:** whether "I found every use" is true.

A search for a name finds the places that spell the name. Python often
uses a function without spelling its name at the call. Before you say
something is unused, safe to delete, or called only from one place, go
through this list. Each item says how to look.

## The list

1. **Decorators that register.** `@app.route("/x")`, `@router.post(...)`,
   `@celery.task`, `@click.command()`, `@pytest.fixture`, `@receiver(...)`,
   or a project's own `@handler("refund")`. The function is stored in a
   table and called from the table. Look for a decorator line above the
   definition, then find what the decorator does with the function
   (`python/dynamic.md`).
2. **Tables and dispatch.** `HANDLERS = {"refund": handle_refund}` then
   `HANDLERS[kind](event)`. Search for the name without a call:
   `\bhandle_refund\b`, and read every hit that is not a call.
3. **Names as strings.** `getattr(obj, name)`, `importlib.import_module(
   path)`, dotted paths in settings such as `"app.jobs.cleanup:run"` or
   `"app.jobs.cleanup.run"`, Django `urls.py` and settings, Celery task
   names, logging configuration, serializers keyed by class name. Search
   for the name inside quotes, in `.py` files and in configuration files.
4. **Entry points in packaging.** `[project.scripts]` and
   `[project.entry-points."group"]` in `pyproject.toml`, `console_scripts`
   in `setup.cfg` or `setup.py`. Plugins are loaded by these names.
5. **Test fixtures by parameter name.** pytest passes a fixture into any
   test whose parameter has the fixture's name. `def test_x(db_session):`
   uses `db_session` without importing it. Look in every `conftest.py` from
   the test's folder up to the root.
6. **Inheritance and overrides.** A method called on a base class runs the
   subclass's version. Search for `def method_name` across all classes,
   and for subclasses of the class: `class \w+\([^)]*\bBase\b`.
7. **Dunder methods.** `__call__`, `__getattr__`, `__enter__`,
   `__iter__`, `__eq__` are called by syntax, not by name.
8. **Module-level `__getattr__` and `__all__`.** A name can be served by a
   function, or pulled in by `from x import *`.
9. **Other repositories.** A library's function may be called by services
   in repositories you do not have open. Use Sourcegraph's
   `find_references` or `keyword_search` across repositories
   (`tools/sourcegraph.md`). Without it, say which repositories were not
   searched.
10. **Generated and vendored code.** Protobuf stubs, ORM migrations, code
    in `vendor/`, templates that call helpers (Jinja `{{ helper() }}`).
11. **Outside the code.** Cron lines, CI workflows, Dockerfiles, shell or
    PowerShell scripts, Makefiles, `tasks.py`, `noxfile.py`, `tox.ini`.

## Verdict

Under *Not covered*, list every item from 1 to 11 that applies to this
code and that you did not rule out, and say why it could not be ruled out.
When all eleven are ruled out, say `none`.

## Never

- Never write "unused" or "safe to delete" after one search for the name.
- Never skip item 9 for a library that other code may depend on.
