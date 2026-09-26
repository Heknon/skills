# Settle a question with a probe

**Verdict you produce:** the question, the probe, and what it printed.

```
question: <one behaviour, such as "does a before validator get an int?">
probe:    probe_<topic>.py, run with uv run --no-sync python probe_<topic>.py
printed:  <the lines that answer it>
versions: pydantic <x>, pydantic-settings <y>, pydantic-partial <z>
```

A probe is the cheapest proof there is. Reading pydantic code is not
enough: the rules that matter (coercion, union choice, which validator
sees what) live in pydantic-core, which is compiled.

## Write it

1. One file per question, in the project folder:
   `probe_<topic>.py`. Never name it after a module: *lab:* a probe
   called `types.py` broke `import typing` (`cannot import name
   'Annotated' from partially initialized module 'typing'`), and one
   called `pydantic.py` broke `from pydantic import BaseModel`.
2. Copy the model in, or import it from the project. Print the outcome
   for each input, valid and invalid, one line each:

```python
from pydantic import ValidationError
from shop.models import Order

for body in [{"id": 1}, {"id": "x"}, {}]:
    try:
        print(body, "->", Order.model_validate(body))
    except ValidationError as e:
        print(body, "->", [(x["type"], x["loc"]) for x in e.errors()])
    except Exception as e:                      # a crash is a finding too
        print(body, "-> CRASH", type(e).__name__, e)
```

3. Print `e.errors()` fields, not `str(e)`: types and locs are short and
   stable; the text carries a URL that cannot be reached air gapped.

## Run it

```
uv run --no-sync python probe_order.py
```

`--no-sync` leaves the environment as it is. With a `src/` layout and
no `[build-system]`, the project is not installed and the import fails
(*lab:* `ModuleNotFoundError: No module named 'profiles'`). Add `src`
to the path for that one run:

```
$env:PYTHONPATH = "src"; uv run --no-sync python probe_order.py; Remove-Item Env:PYTHONPATH
PYTHONPATH=src uv run --no-sync python probe_order.py          # POSIX
```

Write probes to a file rather than `python -c "..."`: PowerShell 5.1
passes quotes inside the argument to native programs differently from
7 (*not run on Windows*).

## Ask the installed source

When the question is "what does this function accept", read the
signature instead of guessing (offline-docs owns the general method):

```python
import inspect
from pydantic import BaseModel, Field
print(list(inspect.signature(Field).parameters))
print(list(inspect.signature(BaseModel.model_dump).parameters))
```

*lab (2.13.5):* `model_dump` takes `mode, include, exclude, context,
by_alias, exclude_unset, exclude_defaults, exclude_none,
exclude_computed_fields, round_trip, warnings, fallback,
serialize_as_any, polymorphic_serialization`. On 2.10.6 the list stops
at `serialize_as_any`, without `fallback` or `exclude_computed_fields`.

## After

Delete the probe file; it is not part of the change. Quote its output in
the answer under **Checked**. If a behaviour matters to the code, turn
the probe into a test.
