# Traceback shapes

**What it decides:** which shape a traceback has, and so which exception
to read first and where. The procedure is `core/read-traceback.md`.

Every block below was produced in the lab on Python 3.12.14 and pasted
as it came. The paths are the lab's: `/home/user/dbg/...` is project
code, `/root/.local/share/uv/python/cpython-3.12.14-.../lib/python3.12/`
is the standard library of a uv-installed Python. On Windows the same
parts look like `C:\...\project\...` and a `...\uv\python\...\Lib\`
folder (not run on Windows). 3.13 and 3.14 differences are in
`python/versions.md`.

## One traceback

Read from the bottom: the last line is the exception type and message;
the frames above it go from the outermost call (top) to the raising
frame (bottom). Each frame is `File "<path>", line <n>, in <function>`,
then the source line, then markers under the part that failed (`^` and
`~`; a line may have none).

```
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/user/dbg/sb/missing-key/sales/__main__.py", line 14, in <module>
    main(sys.argv)
  File "/home/user/dbg/sb/missing-key/sales/__main__.py", line 9, in main
    for region, total in sorted(totals_by_region(rows).items()):
                                ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/user/dbg/sb/missing-key/sales/report.py", line 5, in totals_by_region
    region = row["region"]
             ~~~^^^^^^^^^^
KeyError: 'region'
```

The two `<frozen runpy>` frames are what `python -m` adds; skip them.
The raising frame is the deepest project frame here,
and still not the cause: `row` came from the parser with the key
`'\ufeffregion'` (`core/read-traceback.md` step 5).

## Chain: "During handling of the above exception"

The lower exception was raised inside the `except` block of the upper
one. The upper one came first.

```
Traceback (most recent call last):
  File "/home/user/dbg/tb/chained.py", line 6, in load
    return json.loads(text)
           ^^^^^^^^^^^^^^^^
  File "/root/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu/lib/python3.12/json/__init__.py", line 346, in loads
    return _default_decoder.decode(s)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/root/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu/lib/python3.12/json/decoder.py", line 338, in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/root/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu/lib/python3.12/json/decoder.py", line 354, in raw_decode
    obj, end = self.scan_once(s, idx)
               ^^^^^^^^^^^^^^^^^^^^^^
json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/user/dbg/tb/chained.py", line 12, in <module>
    load("{bad json")
  File "/home/user/dbg/tb/chained.py", line 8, in load
    log = open("/nonexistent/dir/errors.log", "a")
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/nonexistent/dir/errors.log'
```

- First exception: `JSONDecodeError`, raised in the standard library;
  the deepest project frame is `chained.py` line 6: the text passed in
  was not JSON.
- Second: the handler itself failed. Two bugs: the input, and the
  handler. Fixing only the last line leaves the first.
- The first block starts at the `try` frame (`load`), not at
  `<module>`: its caller frames appear only in the second block.

## Chain: "The above exception was the direct cause"

Written as `raise New(...) from exc`: a deliberate wrap. The upper
exception is the detail; the lower one is what the code reported.

```
Traceback (most recent call last):
  File "/home/user/dbg/tb/cause.py", line 7, in read_port
    return int(settings["port"])
               ~~~~~~~~^^^^^^^^
KeyError: 'port'

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/user/dbg/tb/cause.py", line 12, in <module>
    read_port({"host": "db"})
  File "/home/user/dbg/tb/cause.py", line 9, in read_port
    raise ConfigError("port is not set") from exc
ConfigError: port is not set
```

## Hidden: `raise ... from None`

Only the wrapper is printed. Nothing says a cause existed, except the
`raise ... from None` line itself in the last frame.

```
Traceback (most recent call last):
  File "/home/user/dbg/tb/fromnone.py", line 12, in <module>
    read_port({"port": "80a"})
  File "/home/user/dbg/tb/fromnone.py", line 9, in read_port
    raise ConfigError("invalid config") from None
ConfigError: invalid config
```

The hidden exception is still on the object: `from None` sets
`__cause__` to `None` and `__suppress_context__` to `True`, and leaves
`__context__` alone (*lab*, 3.12.14). Print it (`tools/probes.md`) or
run `recipes/locals_on_error.py`, which follows `__context__`. *lab
(from-none):* it was `TOMLDecodeError: Unescaped '\' in a string (at
line 3, column 16)`, a Windows path in a TOML basic string.

## Notes

Lines after the message that are not part of it were added with
`exc.add_note()`:

```
Traceback (most recent call last):
  File "/home/user/dbg/tb/notes.py", line 10, in <module>
    parse(["1", "2", "x3"])
  File "/home/user/dbg/tb/notes.py", line 4, in parse
    int(row)
ValueError: invalid literal for int() with base 10: 'x3'
row 3 of input.csv
```

## Exception group

A `TaskGroup` (or code raising `ExceptionGroup`) collects independent
exceptions. The outer traceback says where the group was raised; each
numbered part is a separate exception with its own traceback. *lab
(task-group sandbox):*

```
  + Exception Group Traceback (most recent call last):
  |   File "<frozen runpy>", line 198, in _run_module_as_main
  |   File "<frozen runpy>", line 88, in _run_code
  |   File "/home/user/dbg/sb/task-group/feeds/__main__.py", line 17, in <module>
  |     asyncio.run(main())
  ...
  |   File "/home/user/dbg/sb/task-group/feeds/__main__.py", line 7, in main
  |     async with asyncio.TaskGroup() as tg:
  |                ^^^^^^^^^^^^^^^^^^^
  ...
  | ExceptionGroup: unhandled errors in a TaskGroup (2 sub-exceptions)
  +-+---------------- 1 ----------------
    | Traceback (most recent call last):
    |   File "/home/user/dbg/sb/task-group/feeds/load.py", line 22, in stock
    |     return {item["sku"]: item["quantity"] for item in feed["items"]}
    |                          ~~~~^^^^^^^^^^^^
    | KeyError: 'quantity'
    +---------------- 2 ----------------
    | Traceback (most recent call last):
    |   File "/home/user/dbg/sb/task-group/feeds/load.py", line 27, in deliveries
    |     return [(item["sku"], date.fromisoformat(item["expected"])) for item in feed["items"]]
    |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    | ValueError: Invalid isoformat string: '2026-10-02T09:00:00Z'
    +------------------------------------
```

(`...` marks asyncio frames cut from this copy.) Two causes, two fixes.
The group line is not an error to fix. After one fix the group remains,
with one sub-exception. In a group, a comprehension's frame is named
after the function around it (`stock`), not `<dictcomp>`: 3.12 inlines
comprehensions.

## Recursion

```
  File "/home/user/dbg/tb/recur.py", line 2, in depth
    return 1 + depth(node.get("parent", node))
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  [Previous line repeated 996 more times]
RecursionError: maximum recursion depth exceeded
```

The repeated frame's arguments never approach the stop condition: here
a node without `"parent"` passes itself.

## Syntax error

No frames, only the file, the line and a caret; the program never ran.

```
  File "/home/user/dbg/tb/syn.py", line 1
    def f(x)
            ^
SyntaxError: expected ':'
```
