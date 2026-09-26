# Stubs: signatures from .pyi files, and their version

**What it decides:** where a stub for a package comes from, which version
it describes, and when it disagrees with the code that runs.

Stubs as a source of *types* for navigation's type questions are
navigation's (`python/types.md` there). Here a stub is a source of
*signatures*: what a function accepts, when the code cannot be read or
has no annotations.

## The kinds, by how far they are from the running code

| Kind | Where | Its version (*lab*) |
| --- | --- | --- |
| inline stub: a `.pyi` next to the module, and `py.typed` | inside the package: `orjson/__init__.pyi`, `orjson/py.typed` | the package's own: shipped in the same wheel as `orjson` 3.12.0 |
| stub package: `types-<name>` installing `<name>-stubs\` | `site-packages\fetchkit-stubs\__init__.pyi` from `types-fetchkit` | its own version: `1.6.0.20260101`; the `METADATA` text says which upstream version it aims at |
| a checker's bundled typeshed | mypy 2.3.1: `site-packages\mypy\typeshed\stdlib` (and `stubs\` with only `librt`, `mypy-extensions`); pyright 1.1.414: `site-packages\pyright\dist\dist\typeshed-fallback\` with `stdlib\` and 201 third-party stub folders | a `METADATA.toml` per folder: `version = "~=2.33.0"` for requests; `commit.txt` names the typeshed commit |
| ty 0.0.84 | no typeshed files in its wheel, only the `ty` binary | not readable on disk |

`types-requests` 2.33.0.20260906 says in its `METADATA`: "This version of
`types-requests` aims to provide accurate annotations for
`requests~=2.33.0`" and "The `requests` package includes type
annotations or type stubs since version 2.34.0. Please uninstall the
`types-requests` package if you use this or a newer version."

## Checkers follow the stub; the interpreter does not

A stub package wins over the package's own types for the checkers, and
means nothing at runtime.

- With requests 2.34.2 (inline types, `py.typed`) and types-requests
  2.33.0.20260906 installed, mypy 2.3.1's `reveal_type(requests.get)`
  showed the stub's signature, with named `data`, `headers`, ...
  parameters; after removing types-requests, it showed requests' own
  `**kwargs: **TypedDict(requests._types.GetKwargs, ...)` (*lab*).
- Eval `stub-mismatch`: types-fetchkit lists `retries: int = 0` for
  `get`. mypy (`Success: no issues found`), pyright (`0 errors`) and ty
  all accepted `fetchkit.get("u", retries=3)`. At runtime fetchkit 2.0.0
  raised `TypeError: _send() got an unexpected keyword argument
  'retries'`, and `inspect.signature(fetchkit.get)` was `(url, **kw)`.

So a stub answers "what does the checker think", and the installed code
answers "what does the call accept". When they differ, the code wins and
the answer says the stub is wrong for this version (`core/evidence.md`).

## Using a stub as the answer

For compiled code there is often nothing better. orjson 3.12.0:

```
orjson/__init__.pyi:10  def dumps(
orjson/__init__.pyi:11      __obj: Any,
orjson/__init__.pyi:12      default: Callable[[Any], Any] | None = ...,
orjson/__init__.pyi:13      option: int | None = ...,
orjson/__init__.pyi:14  ) -> bytes: ...
```

and `inspect.signature(orjson.dumps)` agreed: `(obj, /, default=None,
option=None)`. The stub's `__obj` is positional-only, as the `/` is at
runtime: mypy 2.3.1 said `Unexpected keyword argument "obj" for "dumps"`
for `orjson.dumps(obj={})`, and the interpreter said `dumps() missing 1
required positional argument: 'obj'`. The same mypy run flagged
`sort_keys=True` (`Unexpected keyword argument "sort_keys"`), which is
how this inline stub catches the eval `compiled-stub` bait (*lab*). The
verdict is "confirmed from stub only", naming the stub and the version
of the wheel it came from.

Before using a stub:

1. Is it inline (same wheel, same version) or a separate package? The
   recipe's `pin` prints `pyi:` for stub files in a distribution and
   `stubs: separate stub package at ...` when a `<name>-stubs` folder
   exists.
2. For a separate package, read which version it targets in its
   `METADATA` text and compare with the installed version.
3. Where the runtime has a signature (`inspect.signature`), compare. A
   parameter in the stub and not in the runtime is a stub error.

## The standard library's VERSIONS file

mypy's bundled typeshed has `typeshed\stdlib\VERSIONS`, one line per
module with the Python versions it exists in: `tomllib: 3.11-`,
`asyncio.taskgroups: 3.11-`, `json: 3.0-` (mypy 2.3.1). It answers "since
which Python is this module in the standard library" offline, for the
modules typeshed covers.

## Never

- Never report a parameter from a stub without checking the running code
  when it can be read.
- Never assume a `types-*` package matches the installed version; read
  what it targets.
