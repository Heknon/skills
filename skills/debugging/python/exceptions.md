# What an exception usually means

**What it decides:** for an exception type, what it usually means in
real code, which value to print, and where to search. The procedure is
`core/understand-error.md`.

Every message here was printed in the lab on Python 3.12.14, and
compared on 3.13.15 and 3.14.7; where they differ, the table in *Messages
that change between versions* says so. Library errors ran with pydantic
2.13.5, httpx 0.28.1, SQLAlchemy 2.1.1 (the standard `sqlite3` driver)
and PyMongo 4.18.2 against MongoDB 8.0.32. Windows rows were read in
CPython 3.12.14's source and are marked *not run on Windows*.

## Read the last line in two parts

```
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
<type, with its module>       <message>
```

- **The type decides the meaning.** Match on it, never on the words
  after it: the words change between versions (below) and between
  libraries.
- **The module says whose error it is.** No module (`KeyError`) is a
  built-in; `json.decoder.`, `decimal.` is the standard library;
  `httpx.`, `sqlalchemy.exc.`, `pymongo.errors.` is a library (read its
  installed source with offline-docs); the project's own package is the
  project's. The prefix is where the class lives, not always the
  package's name: pydantic's prints as
  `pydantic_core._pydantic_core.ValidationError` (*lab*).
- **The message names what was asked for, not what was there.**
  `KeyError: 'region'` is the key the code asked for; the dict's keys
  are not in it. Print them.
- **A value in quotes is a `repr`**, so hidden characters show:
  `'﻿12'` is a byte order mark, `'1\xa0000'` a no-break space.

## Messages that change between versions

Never match these by their text, in reasoning, in code or in a test.
*lab*, each on 3.12.14, 3.13.15 and 3.14.7:

| Case | 3.12 | 3.13 | 3.14 |
| --- | --- | --- | --- |
| `json.loads('{"a": 1,}')` | `Expecting property name enclosed in double quotes: line 1 column 9 (char 8)` | `Illegal trailing comma before end of object: line 1 column 8 (char 7)` | as 3.13 |
| `a, b = [1, 2, 3]` | `too many values to unpack (expected 2)` | as 3.12 | `too many values to unpack (expected 2, got 3)` |
| `[1].index(2)` | `2 is not in list` | as 3.12 | `list.index(x): x not in list`: the value is gone from the message |
| two top-level script modules importing each other | `cannot import name 'main' from partially initialized module 'a' (most likely due to a circular import) (.../a.py)` | `cannot import name 'main' from 'a' (consider renaming '.../a.py' if it has the same name as a library you intended to import)`: it no longer says circular | as 3.13 |
| the same cycle inside a package (`app.a`, `app.b`) | `... from partially initialized module 'app.a' (most likely due to a circular import) ...` | as 3.12 | as 3.12 |
| a local `json.py` shadows the standard library | `module 'json' has no attribute 'loads'` | adds `(consider renaming '.../json.py' since it has the same name as the standard library module named 'json' and prevents importing that standard library module)` | as 3.13 |
| `100 // 0` | `integer division or modulo by zero` | as 3.12 | `division by zero` (`python/versions.md`) |

## Messages that hide the cause

The message is true and points the wrong way. *lab (3.12.14):*

| Seen | What was really there | Print |
| --- | --- | --- |
| `KeyError: 'region'` | the key was `'﻿region'`: a CSV with a byte order mark read as `utf-8` | `sorted(row)` at the raise |
| `KeyError: 'price'` | the record changed shape: `{'sku': 'A1', 'quantity': 4, 'pricing': {'unit': 4.5, ...}}` (eval `read-past-the-message`) | the whole record, not only the missing key |
| `KeyError: 0` | a dict indexed as a list: the data became `{"A1": {...}}` | `type(data)` |
| `Expecting value: line 1 column 1 (char 0)` | an empty body, or an HTML page such as a gateway's 502: both print this | `exc.doc[:200]`, or the response's status and content type |
| `decimal.InvalidOperation: [<class 'decimal.ConversionSyntax'>]` | `Decimal("1,50")`: a decimal comma | the text passed in |
| `AttributeError: 'NoneType' object has no attribute 'strip'` | a lookup returned `None`: `COUNTRIES.get("UK")` (eval `keep-the-traceback`) | which call on that line returned `None` |
| `ModuleNotFoundError: No module named 'app'` | `python app/main.py` puts `app/` itself on the path (*lab:* `sys.path[0]` ended in `/app`), not the project root; `python -m app.main` from the root ran | the command, and `sys.path[0]` |
| a log line `failed: 'price'` | a `KeyError`: `str(e)` of a `KeyError` is only the key's `repr`; the type is lost | the log call: `str(e)` or `logger.exception` |

## The common exceptions

| Exception | Usually means in real code | Print | Search |
| --- | --- | --- | --- |
| `KeyError` | the data's shape is not the one the code expects: a renamed or nested field, a byte order mark, a dict where a list was, an unset environment variable (`os.environ[...]`), a `{name}` in `str.format` with no value | the keys that exist, with `repr`: `sorted(d)`; the whole record | where the dict was made: the parser, the response, the file; `git log -S'<key>'` (navigation) |
| `IndexError` | fewer items than expected: a short CSV line, an empty result, `split()` on text without the separator | `len(x)` and `x` itself | where the list was built, and the input line |
| `AttributeError: 'NoneType' ...` | a function returned `None`: `re.match` with no match, `dict.get` with no key, a function missing a `return`, a lookup that found nothing | each call on the line, one at a time | that function's return paths |
| `AttributeError: 'dict' object has no attribute 'name'` | data is a dict where the code expects an object (JSON not turned into a model) | `type(x)` | where the object should have been built |
| `AttributeError: module 'json' has no attribute ...` | a local file shadows a module | `json.__file__` | a file or folder with the module's name in the project |
| `TypeError: f() missing 1 required positional argument` / `takes 2 positional arguments but 3 were given` / `got an unexpected keyword argument` | the caller and the function disagree: an upgraded library, a changed signature | `inspect.signature(f)` of the installed function | the function's definition; for a library, offline-docs `core/signature.md` |
| `TypeError: 'NoneType' object is not subscriptable` / `is not iterable` / `cannot unpack non-iterable NoneType object` | as the `None` row above | the call that returned `None` | its return paths |
| `TypeError: unsupported operand type(s) for +: 'int' and 'str'` | a number that stayed text: read from CSV, JSON or an environment variable | `type()` and `repr()` of both | where the text was read |
| `TypeError: string indices must be integers, not 'str'` | a string where a dict was expected: one level too deep, or JSON not parsed | `type(x)`, `x[:80]` | the loop or the `json.loads` above |
| `TypeError: can't compare offset-naive and offset-aware datetimes` | one datetime has a timezone, the other not | `repr()` of both | where each was made |
| `ValueError` from parsing (`invalid literal for int()`, `could not convert string to float`, `unconverted data remains`, `Invalid isoformat string`) | the text is not in the format the code assumes: a decimal comma, a `T` time, a byte order mark, an empty cell | the text with `repr` | the input line and its source |
| `decimal.InvalidOperation` | as a parse `ValueError`, but it is **not** a `ValueError`: its bases are `DecimalException`, `ArithmeticError` (*lab*); `except ValueError` misses it | the text passed in | `except` clauses around it |
| `ModuleNotFoundError: No module named 'x'` | not installed in the interpreter that ran, or run in a way that leaves the project off the path | `sys.executable`, `sys.path[0]`, the command | navigation `core/environment.md`; packaging when a name differs from its distribution |
| `ImportError: cannot import name 'x' from 'm'` | a circular import, a name removed in an upgrade, or a shadowing file (read the version table: 3.13 blames the file name) | `m.__file__`, and the traceback's import frames | the import lines of both modules |
| `UnicodeDecodeError: 'utf-8' codec can't decode byte ...` / `'charmap' codec ...` | a file read in the wrong encoding; `'charmap'` is a Windows code page such as CP1252 | the encoding used and the first bytes: `open(p, "rb").read(20)` | `open()` calls without `encoding=` (`python/encoding.md`) |
| `UnicodeEncodeError: 'charmap' codec can't encode character` | writing text the code page cannot hold, often printing to a Windows console | `sys.stdout.encoding` | `python/encoding.md` |
| `RecursionError: maximum recursion depth exceeded` | a call that never reaches its stop: a cycle in the data, a property that reads itself (`return self.name` inside `name`) | the repeated frame's arguments | `python/tracebacks.md`, *Recursion* |
| `FileNotFoundError: [Errno 2] ...: 'data/x.csv'` | a relative path from a different current folder, or a wrong name | `os.getcwd()`, `Path(p).resolve()` | where the path is built |
| `PermissionError` | on Windows, often a file another process holds open (below), or a directory opened as a file | the path, and who holds it | Windows rows below |
| `json.decoder.JSONDecodeError` | the text is not JSON: empty, HTML, a byte order mark (`Unexpected UTF-8 BOM (decode using utf-8-sig)`), two documents (`Extra data`) | `exc.doc[:200]`, `exc.pos` | who produced the text: a file, a response (the status first) |
| `TimeoutError`, `ConnectionRefusedError`, `socket.gaierror` | nothing listens there, a firewall, a wrong host or port, a name that does not resolve (air gapped: a public host) | host, port and the setting they came from | the configuration; a client library's own classes below |

`AttributeError`, `NameError` and `ImportError` often end in a hint,
such as `Did you mean: 'name'?` or `Did you forget to import 'sys'?`
(*lab*, all three versions). The hint is printed by the traceback, not
kept in `str(e)`.

## Files on Windows

Read in CPython 3.12.14's source; *not run on Windows*.

- `open()` reports the C runtime's `errno`: `[Errno 13] Permission
  denied: '<path>'` (`Modules/_io/fileio.c` calls `_wopen`, then
  `PyErr_SetFromErrnoWithFilenameObject`).
- `os.remove`, `os.rename` and most `os` functions report the Windows
  error: `[WinError <n>] <Windows' own text>: '<path>'`, with `-> '<dst>'`
  for two paths (`Objects/exceptions.c`, `path_object_error` in
  `Modules/posixmodule.c`). The text is Windows', so match on
  `exc.winerror`, never on the words.
- Which class each Windows error becomes (`PC/errmap.h`, then
  `Objects/exceptions.c`):

  | `winerror` | Name | errno | Class |
  | --- | --- | --- | --- |
  | 2 | `ERROR_FILE_NOT_FOUND` | `ENOENT` | `FileNotFoundError` |
  | 3 | `ERROR_PATH_NOT_FOUND` | `ENOENT` | `FileNotFoundError` |
  | 5 | `ERROR_ACCESS_DENIED` | `EACCES` | `PermissionError` |
  | 32 | `ERROR_SHARING_VIOLATION` | `EACCES` | `PermissionError`: another process has the file open |
  | 33 | `ERROR_LOCK_VIOLATION` | `EACCES` | `PermissionError` |

- Opening a directory as a file: Windows gives `[Errno 13]`, Linux
  `[Errno 21] Is a directory` (`Lib/test/test_fileio.py`, `testOpendir`;
  *lab, Linux:* `IsADirectoryError: [Errno 21] Is a directory: '.'`).

So a `PermissionError` on Windows is often not about rights: print
`exc.winerror` and ask what else has the file open (an editor, a
previous run, a virus scanner).

## Clients: connections and timeouts

*lab (3.12.14):*

| Client | Nothing listening | No answer in time |
| --- | --- | --- |
| `socket` | `ConnectionRefusedError: [Errno 111] Connection refused` | `TimeoutError: timed out` |
| `urllib.request` | `urllib.error.URLError: <urlopen error [Errno 111] Connection refused>` (a subclass of `OSError`) | `TimeoutError: timed out` |
| httpx 0.28.1 | `httpx.ConnectError: [Errno 111] Connection refused` | `httpx.ReadTimeout: timed out` |
| PyMongo 4.18.2 | `ServerSelectionTimeoutError: 127.0.0.1:27018: [Errno 111] Connection refused (configured timeouts: ...), Timeout: 0.5s, Topology Description: ...`, raised after `serverSelectionTimeoutMS` | not run |

- **httpx's errors are not the built-in ones.** *lab:* `isinstance(e,
  ConnectionError)` and `isinstance(e, OSError)` were `False` for
  `httpx.ConnectError`, and `isinstance(e, TimeoutError)` was `False`
  for `httpx.ReadTimeout`. Their bases: `ConnectError`, `NetworkError`,
  `TransportError`, `RequestError`, `HTTPError`. An `except
  ConnectionError` or `except TimeoutError` never catches them.
- A name that does not resolve: `socket.gaierror: [Errno -2] Name or
  service not known` on Linux (*lab*); Windows prints its own number and
  text (*not run on Windows*).
- Errno 111 is Linux's number for a refused connection. On Windows,
  CPython defines `ECONNREFUSED` as `WSAECONNREFUSED`, 10061, and maps
  it to the same `ConnectionRefusedError` (`Objects/exceptions.c`, *not
  run on Windows*). Match on the class, not the number.

## Library errors: the shape, and what to print

Each owner skill says what the error means in its domain; this table
says how to read it and what it leaks. Settle anything else from the
installed source (offline-docs `core/behaviour.md`).

| Error | `str(e)`, *lab* | Keep and print | Leaks into logs | Owner |
| --- | --- | --- | --- | --- |
| pydantic `ValidationError` (a `ValueError`) | `2 validation errors for Login`, then per field: `password` / `String should have at least 12 characters [type=string_too_short, input_value='hunter2', input_type=str]` | `e.errors()`: `loc`, `type`, `input`; `e.error_count()` | `input_value`: the password above. `hide_input_in_errors=True` in the model's config removes it (*lab*) | pydantic `core/read-error.md` |
| httpx `HTTPStatusError` | `Client error '404 Not Found' for url 'http://reports.internal/v1/missing?token=tok_live_9f2c'` and a line `For more information check: https://developer.mozilla.org/...` | `e.response.status_code`, `e.response.text[:200]`, `e.request.url.path` | the whole URL with its query string: the token above | api for status meaning |
| SQLAlchemy `IntegrityError` | `(sqlite3.IntegrityError) UNIQUE constraint failed: users.email` / `[SQL: INSERT INTO users (email, name) VALUES (?, ?)]` / `[parameters: ('ana@example.com', 'Ana B')]` / `(Background on this error at: https://sqlalche.me/e/21/gkpj)` | `e.orig` (the driver's error), `e.params`, `e.statement` | the row's values. `create_engine(..., hide_parameters=True)` prints `[SQL parameters hidden due to hide_parameters=True]` (*lab*) | architecture `sqlalchemy/errors.md` (translating it) |
| PyMongo `DuplicateKeyError` (bases `WriteError`, `OperationFailure`) | `E11000 duplicate key error collection: lab.users index: email_1 dup key: { email: "ana@example.com" }, full error: {...}` | `e.code` (11000), `e.details["keyPattern"]`, `e.details["keyValue"]` | the duplicated value, twice | mongodb `core/writes.md`; architecture for translating it |

`response.json()` on a 502 HTML page raises the standard library's
`JSONDecodeError`, not an httpx error (*lab*): read the status before
the body (`examples/understand-an-error.md`).

## Errors without a traceback

| You have | Get the evidence with |
| --- | --- |
| a log line with only a message | find the call that wrote it (search for its fixed text); if it logs `str(e)`, rerun with `logger.exception` there as a probe, or call the failing function directly. *lab:* `log.error(f"... {e}")` of a `KeyError` printed `import failed: 'price'`; `%r` printed `KeyError('price')`; `log.exception(...)` printed the traceback |
| an exit code | `core/crash.md`, step 1. Also, *lab:* 2 with `usage:` above is `argparse`; `sys.exit("config missing")` prints the text and exits 1; `python -m no_such_module` exits 1. A 0 with `ERROR` lines means the code caught the error and went on (eval `keep-the-traceback`) |
| an HTTP status | print the status, the `content-type` and the first 200 characters of the body. 4xx: the request was refused; its body usually says why. 5xx: the server failed; its log has the traceback. 502 or 504 with an HTML body: a gateway could not reach the service. What each status means is api's `core/methods-and-status.md` |
| a wrong value, no error | `core/reproduce.md`: the reproduction checks the value. Print `repr()` and `type()` of the value next to the right one: `'10'` against `10`, a `float` against a `Decimal`, a naive against an aware datetime |
