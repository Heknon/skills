# Worked example: a compiled library, answered from its stub

Kinds: Signature, Discover. Verdict: confirmed from stub only. Commands
and output from a lab run of eval `compiled-stub` (Linux, uv 0.12.19,
CPython 3.12.14); `.../site-packages` stands for
`/home/user/od-lab/ex2/.venv/lib/python3.12/site-packages`.

## The ask

> Make `export_report` in `app/export.py` sort the keys and indent by 2
> spaces, like `json.dumps(sort_keys=True, indent=2)`. What does
> `orjson.dumps` accept?

Memory of `json.dumps` suggests `orjson.dumps(report, sort_keys=True,
indent=2)`. In the lab that raised `TypeError: dumps() got an unexpected
keyword argument`.

## Steps

1. **Pin**:

   ```
   > uv run --no-sync python <skill>\recipes\lookup.py pin orjson
   python:    3.12.14 at /home/user/od-lab/ex2/.venv/bin/python
   dist:      orjson 3.12.0
   ...
   import:    orjson -> .../site-packages/orjson/__init__.py (source)
   compiled:  1 file(s) in the package, such as orjson.cpython-312-x86_64-linux-gnu.so
   typed:     orjson ships py.typed
   pyi:       1 stub file(s) in this distribution, such as orjson/__init__.pyi
   ```

   The `__init__.py` only re-exports (`from .orjson import *`); the code
   is in the compiled module. The stub ships in the same wheel, so it is
   for 3.12.0 (`python/stubs.md`).

2. **Ask the runtime** (`python/inspect.md`):

   ```
   > uv run --no-sync python <skill>\recipes\lookup.py def orjson.dumps
   imported:  orjson (its top-level code ran)
   object:    builtins.builtin_function_or_method
   signature: (obj, /, default=None, option=None)
   source:    none (TypeError: module, class, method, function, traceback, frame, or code object was expected, got builtin_function_or_method); read a stub or the docstring
   module:    orjson at .../site-packages/orjson/__init__.py
   doc:       Serialize Python objects to JSON.
   ```

   Three parameters; no `sort_keys`, no `indent`. No source to read.

3. **Read the stub**:

   ```
   > uv run --no-sync python <skill>\recipes\lookup.py lines .../site-packages/orjson/__init__.pyi 10 14
      10  def dumps(
      11      __obj: Any,
      12      default: Callable[[Any], Any] | None = ...,
      13      option: int | None = ...,
      14  ) -> bytes: ...
   ```

   The stub also lists `OPT_INDENT_2: int` (line 24) and
   `OPT_SORT_KEYS: int` (line 34).

4. **Find what replaces the json keywords** (`core/discover.md`): the
   recipe's `grep` searches the `METADATA` text too.

   ```
   > uv run --no-sync python <skill>\recipes\lookup.py grep orjson "sort_keys|indent"
   .../site-packages/orjson-3.12.0.dist-info/METADATA:166: `sort_keys` is replaced by `option=orjson.OPT_SORT_KEYS`.
   .../site-packages/orjson-3.12.0.dist-info/METADATA:168: `indent` is replaced by `option=orjson.OPT_INDENT_2` and other levels of indentation are not
   ...
   7 match(es) for /sort_keys|indent/ in 3 file(s) under .../site-packages/orjson and its METADATA
   ```

   Line 169 ends the sentence: `supported.` Only two-space indentation
   exists.

5. **Change and run it**: `orjson.dumps(report, option=orjson.OPT_SORT_KEYS
   | orjson.OPT_INDENT_2)`.

   ```
   > uv run --no-sync python -c "from app.export import export_report; print(export_report({'b': 1, 'a': [1, 2]}).decode())"
   {
     "a": [
       1,
       2
     ],
     "b": 1
   }
   ```

## The answer

```
## Answer
Answer:   orjson.dumps(obj, /, default=None, option=None) -> bytes. Sorting and
          indenting are flags in option: OPT_SORT_KEYS | OPT_INDENT_2 (2 spaces
          is the only indent). export_report now passes them.
Checked:  orjson 3.12.0, Python 3.12.14, /home/user/od-lab/ex2/.venv/bin/python
Evidence: orjson/__init__.pyi:10-14 def dumps(__obj, default=..., option=...);
          inspect.signature: (obj, /, default=None, option=None);
          orjson-3.12.0.dist-info/METADATA:166-169 sort_keys and indent are replaced
          by the options; run: keys sorted, 2-space indent
Source:   stub
Verdict:  confirmed from stub only (orjson/__init__.pyi, shipped in orjson 3.12.0),
          with the METADATA text and a run

## Not checked
- The compiled code itself: not readable on the machine.
- export_report returns bytes, as before; callers were not changed.
```
