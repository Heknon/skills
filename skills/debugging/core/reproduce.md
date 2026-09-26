# Reproduce

**Verdict you produce:** one command and what it shows, before any edit.

```
command:  <exactly what was run, from which folder>
result:   <exit code and the symptom's line, copied: "exit 1, KeyError: 'region'">
rate:     <"every time", or "k of N runs" (core/intermittent.md)>
matches:  <yes: the same message and place as the report | no: <what differs>>
```

A reproduction is the only evidence that a fix fixed anything. Without
one, the fix is a guess and its proof is impossible (`core/prove-the-fix.md`).

## Steps

1. **Run what was reported, as reported**, from the folder it is run
   from, through uv (`uv run python -m sales data/may.csv`). Copy the
   result. If it fails the same way, this is the reproduction; go to
   step 5.
2. **If there is no command**, build the smallest call that shows the
   symptom, with the input from the report:

   ```powershell
   uv run python -c "from shop.shipping import shipping_cost; print(shipping_cost([12.50, 37.50]))"
   ```

   *lab (two-suspects):* printed `4.95` where the ticket says free.
3. **A wrong value with no error needs the right value next to it.**
   Work it out from the requirement, not from the code: "dune: 3 x 4.00 =
   12.00, printed 37.50" (*lab*, wrong-totals). The reproduction prints
   both or exits 1 when they differ.
4. **Make it a script when it will be run more than twice**: while
   shrinking, proving, counting or bisecting. Copy
   `recipes/repro_template.py` and change its three marked parts. It
   exits 0 when the bug is absent, 1 when present, 125 when the code
   cannot be tested. Run it from the project root:

   ```powershell
   uv run python ..\repro_bom.py; $LASTEXITCODE
   ```

5. **Check it fails for the reported reason.** The same exception, the
   same message, the same line. A different error is a different bug, or
   a broken reproduction: fix the reproduction first.
6. **Check it cannot wait.** Nothing in the path may stop for the
   keyboard: search for `breakpoint(`, `pdb`, `input(` first, and run
   with `$env:PYTHONBREAKPOINT = "0"` if one is there (`tools/pdb.md`).
   Anything that might hang runs under a time limit
   (`recipes/watchdog.py`, `tools/powershell.md`).
7. **If it passes**, the bug is not reproduced yet. Do not edit. Either
   the case differs from the report (the input, the data file, the
   order of calls) or the environment does: `core/differ.md`. If it
   fails only sometimes: `core/intermittent.md`.

## Facts the lab found

- **A script outside the project cannot import it** unless the project
  folder is on `sys.path`: `python ..\repro.py` puts the script's own
  folder there, not the current one. *lab (regression):* every commit
  returned `SKIP (125): cannot import: ModuleNotFoundError("No module
  named 'units'")`, and the bisect named nothing. The template inserts
  `os.getcwd()` for this reason; run it from the project root.
- **Output printed before a crash can be lost.** With stdout sent to a
  file or a pipe, Python buffers it; a crash throws the buffer away.
  *lab (3.12.14):* `print("reading")` then a segfault left an empty
  file; with `-u` or `PYTHONUNBUFFERED=1` the line was kept. stderr is
  not held back this way (*lab:* a line printed to stderr survived the
  same crash). Print reproduction output to stderr, or run with `-u`.
- **The exit code is part of the symptom.** A thread that dies does not
  change it (*lab:* `imported 12 of 31 lines`, exit 0), nor does an
  unretrieved `concurrent.futures` exception (exit 0, nothing printed).
  Check both the output and `$LASTEXITCODE`.

## Never

- Never edit the code "to see if it helps" before the reproduction
  fails.
- Never accept "it did not fail for me" as "fixed". A reproduction that
  passes before the fix proves nothing about the fix.
- Never build the expected value by running the code; take it from the
  requirement, the ticket, a docstring, or arithmetic.

## Stop and ask

- The failing input is private or unavailable (a customer file, a
  production database): ask for the smallest sample that fails, or for
  its first bytes and shape.
