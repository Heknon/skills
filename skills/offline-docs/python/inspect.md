# inspect: signatures and source, and where they fail

**What it decides:** what `inspect.signature`, `inspect.getsource` and
`inspect.getsourcefile` tell you about an object, and when their answer
is missing or points at code that does not run.

All results are from CPython 3.12.14 (*lab*). The recipe's `def` command
runs these and falls back where they fail.

## The calls

```powershell
uv run --no-sync python -c "import inspect, json; print(inspect.signature(json.dumps))"
uv run --no-sync python -c "import inspect, json; print(inspect.getsourcefile(json.dumps), inspect.getsourcelines(json.dumps)[1])"
uv run --no-sync python -c "import inspect, json; print(inspect.getsource(json.dumps))"
```

## Builtins and C functions

A compiled function has a signature only if its author wrote a text
signature (`__text_signature__`). None of them has Python source.

| Object | `inspect.signature` | `getsourcefile` |
| --- | --- | --- |
| `len`, `sorted`, `print`, `open`, `math.sqrt`, `dict.get`, `str.split` | works: `(obj, /)`, `(iterable, /, *, key=None, reverse=False)`, ... | TypeError |
| `max`, `min`, `getattr`, `iter`, `next`, `functools.reduce`, `math.log` | `ValueError: no signature found for builtin <built-in function max>` | TypeError |
| the classes `dict`, `int`, `str`, `range`, `zip`, `map`, `type`, `itertools.islice` | `ValueError: no signature found for builtin type <class 'dict'>` | TypeError |
| `socket.socket.settimeout` | `ValueError: no signature found for builtin <method 'settimeout' of '_socket.socket' objects>` | TypeError |
| `orjson.dumps` (orjson 3.12.0) | works: `(obj, /, default=None, option=None)` | TypeError |
| `pydantic.BaseModel.dict` (pydantic 1.10.26, Cython) | works, with the annotations | TypeError: `...got cython_function_or_method` |

The TypeError reads `module, class, method, function, traceback, frame,
or code object was expected, got builtin_function_or_method`.

When the signature fails, the docstring's first line often holds it:
`socket.socket.settimeout.__doc__` starts `settimeout(timeout)` and says
`Setting a timeout of None disables the timeout feature`. Read it with
`render_doc` (`python/pydoc.md`); the verdict is then "confirmed from
help only".

A Cython function keeps a code object: `pydantic.BaseModel.dict.__code__`
gave `co_filename` `pydantic/main.py` and `co_firstlineno` 450, the `def`
in the `.py` shipped beside the compiled module. The recipe prints that as
`compiled from <path>:450`.

## Source that is not the code that runs

`getsourcefile` works from the object's `__module__`, so it can name a
Python file for a class that is compiled:

| Object | `getsourcefile` | `getsource` | What runs |
| --- | --- | --- | --- |
| `datetime.datetime` | `.../lib/python3.12/datetime.py` | `OSError: could not find class definition` | the C class from `_datetime` (`datetime.py:2`: `from _datetime import *`) |
| `collections.deque` | `.../collections/__init__.py` | `OSError: could not find class definition` | the C class from `_collections` |
| `collections.OrderedDict` | `.../collections/__init__.py` | **returns** `class OrderedDict(dict):`, line 83 | the C class: line 340 does `from _collections import OrderedDict`, and `collections.OrderedDict is _collections.OrderedDict` was `True` |

So before quoting standard library source, check the module does not
replace it: search the file for `from _` imports after the definition.
The Python version is a fallback with the same intent, not the running
code; say so in the answer.

## Decorated functions

`signature` and `getsourcelines` follow `__wrapped__`, set by
`functools.wraps`. `core/signature.md` has the three cases recorded; in
short, `signature(f, follow_wrapped=False)` shows the wrapper's own
`(*args, **kwargs)`, and a wrapper that supplies an argument itself makes
the followed signature wrong for callers.

## Methods and classes

- `inspect.signature(SomeClass)` gives the parameters of the call that
  makes an instance, from `__init__` or `__new__`, without `self` or
  `cls`: `(x, y=2)` and `(z)` in the lab. A pydantic 1.10.26 model gives
  its fields: `(*, status: str | None = None, note: str | None = None,
  quantity: int | None = None) -> None` for `OrderPatch`.
- For a method, ask the class attribute (`pydantic.BaseModel.dict`); the
  signature then starts with `self`.

## Never

- Never read a missing signature as "takes no arguments".
- Never quote `getsource` output as the running code without checking the
  module does not replace it with a compiled one.
