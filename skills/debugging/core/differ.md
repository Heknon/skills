# Works here, fails there

**Verdict you produce:** the one difference that decides the result,
shown by flipping it.

```
passes:     <where, with the command and its result>
fails:      <where, with the command and its result>
differences:<the list, each with the evidence on both sides>
flipped:    <one difference changed on one side> -> <the result followed it: fails / passes>
cause:      <the code that depends on that difference, file:line>
```

"Cannot reproduce" is a finding, not an answer. Two runs of the same
code that end differently differ in something. List every difference
you can see, then change one at a time until the result follows.

## Steps

1. **Get both results as evidence**: your own run, and the failing one
   (a CI log, the person's paste, a pod log). Copy the failing line.
2. **List the differences.** Read each side from output, not memory:

   | Difference | Read it with |
   | --- | --- |
   | Python version, OS | the CI log header; `uv run python -c "import sys, platform; print(sys.version, platform.system())"` |
   | text encoding | `uv run python -c "import locale, sys; print(locale.getencoding(), sys.flags.utf8_mode)"` |
   | package versions | `uv pip list` on both sides, or the lock file each used; why they resolved differently is the packaging skill's |
   | which interpreter and packages actually run | the navigation skill's Environment procedure (`core/environment.md`) |
   | environment variables | the ones the code reads: search for `os.environ`, `getenv` |
   | input data | the file's first bytes (`core/shrink.md`), its size, its line endings |
   | configuration files | which file was read, and its values on both sides |
   | current folder, paths | `os.getcwd()`; relative paths, `\` against `/`, case of file names |
   | time, time zone | `time.tzname`; tests near midnight, month ends, daylight saving |
   | order and parallelism | test order and workers are pytest's (`core/flaky-and-slow.md`); threads in the code are `core/intermittent.md` |

3. **Pick the difference most likely to matter, and flip it on the side
   you control**: set the variable, use the other version, copy the
   other side's input. Change one thing, run, record. For another Python
   version use `uv run --isolated --python 3.13 pytest -q`. *lab (uv
   0.12.19):* without `--isolated`, `uv run --python 3.13` replaced the
   project's `.venv`, and later plain `uv run` commands kept using 3.13;
   with it, a temporary environment was used and `.venv` stayed on 3.12.
4. **The result must follow the flip both ways**: flipped, it fails;
   flipped back, it passes. Then the difference is the cause's trigger;
   find the code that depends on it.
5. **If nothing flips it**, the difference is one you have not listed:
   list more, or `core/intermittent.md` if it fails only sometimes.

## The encoding flip

The commonest difference between a Linux runner and a Windows machine:
`open()` without `encoding=` uses the locale's code page, so the same
file reads differently. *lab (utf8-ci, Python 3.12.14, a CP1252 locale
standing in for Windows):*

| Run | `locale.getencoding()`, UTF-8 mode | Test |
| --- | --- | --- |
| Linux runner | `UTF-8`, 1 | passed |
| CP1252 locale | `CP1252`, 0 | `UnicodeDecodeError: 'charmap' codec can't decode byte 0x81 in position 1` |
| CP1252 locale, `PYTHONUTF8=1` | `CP1252`, 1 | passed |

The flip is `$env:PYTHONUTF8 = "1"` and back with
`Remove-Item Env:PYTHONUTF8` (not run on Windows). It proves the cause;
it is not the fix. The fix is `encoding="utf-8"` in the `open()` call.
`PYTHONWARNDEFAULTENCODING=1` makes every such call warn, even on the
side that passes (*lab:* `names/load.py:3: EncodingWarning: 'encoding'
argument not specified` in pytest's warnings summary). More in
`python/encoding.md`.

## Never

- Never say "cannot reproduce" and stop, or declare it fixed because it
  passes here.
- Never blame the other machine, CI or "the environment" without the
  flip that shows which part of it.
- Never make the flip the fix (a variable set in CI, a pinned locale)
  when the code can stop depending on it.

## Stop and ask

- The failing side cannot be observed at all (no log, no access): say
  which command, run there, would settle each listed difference.
