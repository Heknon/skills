# Memory

**Verdict you produce:** the allocation site that grows, from two
snapshots, and what holds the references.

```
measured:   <the command: which function, how many rounds between snapshots>
grows at:   <file:line, size and count added, copied from the diff>
held by:    <the container or reference that keeps it alive: "module-level dict _rendered">
why:        <why it never shrinks: "the key includes the request id, so every request adds an entry">
after fix:  <the same measurement: no growth>
```

Memory that keeps growing is almost never Python "not freeing". Every
object still referenced is kept on purpose; the question is which
reference. `tracemalloc` shows the line that allocated what grew; the
code around that line shows where it was put.

## Steps

1. **Reproduce the growth in one process**: call the code that runs per
   request, per message or per file many times in a loop. A simulator
   or a test client is enough; the production process is not needed.
2. **Take two snapshots** with a warm-up first, so imports and
   first-time caches do not count:

   ```powershell
   uv run python ..\mem_diff.py profiles.serve:serve 1000
   ```

   `recipes/mem_diff.py` calls the function once, snapshots, calls it
   `--rounds` more times, snapshots again, and prints the lines that
   grew most (`tools/tracemalloc.md`). *lab (growing-cache):*

   ```
   5 rounds of profiles.serve:serve(1000,): +2095.8 KiB in total
   /root/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu/lib/python3.12/json/encoder.py:258: size=1720 KiB (+1434 KiB), count=6000 (+5000), average=294 B
   /home/user/dbg/sb/growing-cache/profiles/render.py:16: size=324 KiB (+273 KiB), count=5924 (+5000), average=56 B
   /home/user/dbg/sb/growing-cache/profiles/render.py:19: size=288 KiB (+252 KiB), count=1 (+0), average=288 KiB
   ```

   5 000 calls, `+5000` blocks: one object kept per call.
3. **If the top line is in a library**, group by several frames to see
   which project line called it: `--frames 4`. *lab:* the json line
   belonged to `render.py` line 19, `_rendered[key] = json.dumps(...)`.
4. **Find what holds it.** Read the project line: where does the new
   object go? A module-level dict or list, a class attribute, a cache
   decorator, a list of callbacks, a closure kept by a long-lived
   object. The growing `count` with one big block at the container's
   line (`count=1`, growing size) is the container resizing.
5. **Ask why it never shrinks**: a key that is unique per call (a
   request id, a timestamp, an object), no size limit, entries never
   removed. *lab:* the cache key was `(user_id, request_id)`; its
   docstring said "cached per user".
6. **Fix the holder**: the right key, a bound (`functools.lru_cache
   (maxsize=...)`, a size check), removal when done, or no cache.
7. **Prove it** with the same measurement: *lab:* after keying by
   `user_id`, `+0.0 KiB in total`; with the fix reverted, `+2095.8 KiB`
   again.

## `gc.collect()` is not a fix

The garbage collector frees objects that are unreachable, such as
reference cycles. It cannot free what a live dict still holds. *lab:*
calling `gc.collect()` after every 1 000 requests, the traced memory
still grew by 2 084 KiB over 5 000 requests. Show this measurement when
someone proposes it.

## Never

- Never add `gc.collect()`, a restart schedule or a larger memory limit
  as the fix for growth that a snapshot diff has not explained.
- Never judge from one snapshot: sizes mean nothing without the second.
- Never leave `tracemalloc.start()` in the code; it slows every
  allocation.
