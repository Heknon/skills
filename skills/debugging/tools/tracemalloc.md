# tracemalloc

**What it decides:** which source lines allocated the memory that is
still held, and which of them grew. Standard library; checked on
3.12.14. The procedure is `core/memory.md`; the ready script is
`recipes/mem_diff.py`.

## Start it

| Form | Effect |
| --- | --- |
| `tracemalloc.start()` | trace from now on, 1 frame per allocation |
| `tracemalloc.start(25)` | keep 25 frames, to see who called the allocating line |
| `uv run python -X tracemalloc=25 app.py` | the same from the start of the process |
| `$env:PYTHONTRACEMALLOC = "25"` | the same for every Python started from this shell |

Only allocations made after it starts are traced. Everything runs
slower while it is on.

## Two snapshots and a diff

```python
before = tracemalloc.take_snapshot()
# ... run the code that should not grow, many times ...
after = tracemalloc.take_snapshot()
for stat in after.compare_to(before, "lineno")[:10]:
    print(stat)
```

Each line reads (*lab*):

```
/home/user/dbg/sb/growing-cache/profiles/render.py:16: size=324 KiB (+273 KiB), count=5924 (+5000), average=56 B
```

`size` and `count` are what that line holds now; the numbers in
brackets are the growth since the first snapshot. A count that grows by
the number of calls means one object kept per call.

- `"lineno"` groups by the allocating line; `"traceback"` groups by the
  whole kept stack (needs `start(n)` with n > 1), which shows the
  project line under a library line (*lab:* `json/encoder.py:258` was
  called from `render.py` line 19).
- `snapshot.filter_traces([tracemalloc.Filter(False, tracemalloc.__file__)])`
  drops tracemalloc's own allocations; `mem_diff.py` also drops its own
  file and the import machinery.
- `tracemalloc.get_traced_memory()` returns `(current, peak)` in bytes.

## Never

- Never compare one snapshot with nothing: growth needs two.
- Never take the first snapshot before a warm-up call: imports and
  first-time caches then look like a leak.
- Never leave `tracemalloc.start()` in the code.
