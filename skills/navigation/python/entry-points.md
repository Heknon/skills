# Python entry points: how the program starts

**What it decides:** every way the code in this repository is started,
each with the file and line that defines it.

## Where to look, in order

| Where | What to search or read | It means |
| --- | --- | --- |
| `pyproject.toml` `[project.scripts]` | read the table | a command `name = "pkg.module:function"` |
| `pyproject.toml` `[project.entry-points."<group>"]` | read the table | plugins loaded by group name |
| `setup.cfg` `[options.entry_points]`, `setup.py` `entry_points=` | read | the same, older packaging |
| `pyproject.toml` `[tool.poetry.scripts]` | read | poetry's command table |
| `__main__.py` in a package | `find_path` for `**/__main__.py` | `python -m <package>` runs it |
| `if __name__ == "__main__":` | grep `^if __name__ == .__main__.:` | the file is run directly |
| `Dockerfile` | `CMD`, `ENTRYPOINT` lines | how the container starts it |
| `docker-compose*.yml`, `Procfile` | `command:` lines, process lines | how each service starts |
| CI workflows, `Makefile`, `justfile`, `tasks.py`, `noxfile.py`, `tox.ini` | the commands they run | how tests and tools are started |
| `manage.py`, `wsgi.py`, `asgi.py` | exist or not | a Django project; `manage.py` is its command entry |

This file finds entry points. Declaring a console script, or fixing one
that fails once installed, is the packaging skill's `core/entry-points.md`.

## Web applications

- **The app object**: grep `=\s*(FastAPI|Flask|Starlette|Sanic|Quart)\(`
  and `get_wsgi_application|get_asgi_application`.
- **How it is served**: a string `"module.path:app"` passed to `uvicorn`,
  `gunicorn`, `hypercorn`, or `waitress`. Search for `:app"` and for those
  server names in scripts, Dockerfiles and `pyproject.toml`.
- **Routes**: decorators such as `@app.get("/x")`, `@router.post("/x")`,
  `@app.route("/x", methods=[...])`, `@bp.route`. A router's full path is
  its own prefix plus every prefix it is included under:
  `APIRouter(prefix="/orders")`, `app.include_router(router,
  prefix="/api")`, `Blueprint(..., url_prefix="/orders")`,
  `app.register_blueprint(bp, url_prefix=...)`. Django: `urls.py` with
  `path("orders/<int:id>/", view)` and `include("app.urls")`.
- **Finding the handler for a URL**: split the URL at each prefix. Search
  for the last segment's pattern in route decorators, then confirm the
  prefixes it is included under add up to the full URL. A search for the
  full URL string almost never matches, because the parts live in
  different files.

## Command line tools

- `argparse`: grep `ArgumentParser\(` and `add_subparsers`. Each
  subcommand's handler is usually set with `set_defaults(func=...)`.
- `click`: `@click.command`, `@click.group`, `@<group>.command`.
- `typer`: `typer.Typer()`, `@app.command()`.

## Workers and schedulers

Celery (`@app.task`, `@shared_task`, `celery -A`), RQ, Dramatiq, APScheduler,
cron lines in files or containers. The task function is called by the
worker, by name; see `python/dynamic.md`.

## Tests

pytest collects `test_*.py` and `*_test.py`, functions named `test_*`,
and classes named `Test*`, from the folders in `testpaths` if set
(`[tool.pytest.ini_options]` in `pyproject.toml`, or `pytest.ini`).
Fixtures come from `conftest.py` files in the test's folder and every
folder above it, up to the root.
