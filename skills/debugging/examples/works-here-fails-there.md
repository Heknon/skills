# Worked example: green in CI, red on the laptop

Kinds: Differ, Fix. Outputs are from a lab run on Python 3.12.14 and
pytest 9.1.1 in a copy of the `utf8-ci` sandbox. The laptop was stood
in for by a CP1252 locale on Linux (`LOCPATH` and `LC_ALL` pointing at a
locale built with `localedef -f CP1252`); the PowerShell lines are the
forms to type on Windows and were not run there.

## The ask

> test_load_names fails on my Windows laptop with UnicodeDecodeError, but
> CI is green (the log is in ci-log.txt). CI runs the same code, so is my
> machine broken?

## Steps

1. **Reproduce on the failing side** (`core/reproduce.md`):

   ```
   $ uv run pytest -q
   E       UnicodeDecodeError: 'charmap' codec can't decode byte 0x81 in position 1: character maps to <undefined>
   1 failed in 0.02s
   ```

2. **List the differences** (`core/differ.md`), from evidence on both
   sides. CI's log starts with the probe line; the laptop's is run here:

   ```
   ci-log.txt:  linux 3.12.14 UTF-8
   laptop:      3.12.14 Linux CP1252 0      (version, system, locale.getencoding(), utf8_mode)
   ```

   Same Python and code; different operating system and text encoding.
   The error is a decoding error, so the encoding goes first.
3. **Flip one difference, both ways**:

   ```powershell
   $env:PYTHONUTF8 = "1"
   uv run pytest -q                 # 1 passed in 0.00s
   Remove-Item Env:PYTHONUTF8
   uv run pytest -q                 # 1 failed in 0.02s
   ```

   The result follows UTF-8 mode: the encoding decides it.
4. **Find the code that depends on it**:

   ```powershell
   $env:PYTHONWARNDEFAULTENCODING = "1"; $env:PYTHONUTF8 = "1"
   uv run pytest -q
   ```

   ```
     /home/user/dbg/ex2/names/load.py:3: EncodingWarning: 'encoding' argument not specified
   1 passed, 1 warning in 0.00s
   ```

   `names/load.py` line 3, `open(path)`, reads a UTF-8 file with the
   machine's code page. `Á` is `c3 81` in UTF-8, and `0x81` has no
   character in CP1252. (Remove both variables after.)
5. **Fix it**: `open(path, encoding="utf-8")`.
6. **Prove it on the failing side, with UTF-8 mode off**
   (`core/prove-the-fix.md`):

   ```
   $ uv run pytest -q                      1 passed in 0.00s
   $ PYTHONUTF8=0 uv run pytest -q         1 passed in 0.00s
   $ git stash push -- names/load.py
   $ uv run pytest -q                      1 failed in 0.02s
   $ git stash pop
   $ uv run pytest -q                      1 passed in 0.01s
   ```

   With `PYTHONWARNDEFAULTENCODING=1` the warning is gone, and on the
   UTF-8 side the test still passes.

## The answer

```
## Cause
names/load.py line 3 opens the file with open(path) and no encoding.
Python then uses the machine's code page: UTF-8 on the Linux runner,
CP1252 on the laptop. customers.txt is UTF-8; its byte 0x81 (from "Á")
does not exist in CP1252. Your machine is not broken; the code depends
on it.

## Reproduction
uv run pytest -q on the laptop -> UnicodeDecodeError: 'charmap' codec
can't decode byte 0x81 in position 1. Flip: with PYTHONUTF8=1 it passes,
without it fails again.

## Fix
names/load.py: open(path, encoding="utf-8").

## Proof
With the fix: 1 passed, also with PYTHONUTF8=0. With the fix stashed:
1 failed with the same UnicodeDecodeError. Restored: 1 passed. On the
UTF-8 side: 1 passed.

## Result
names/load.py changed; no test changed.

## Checked
The four runs above; PYTHONWARNDEFAULTENCODING=1 shows no warning after
the fix.

## Not checked
The real Windows laptop: the lab used a CP1252 locale on Linux.

## Done when
test_load_names passes on the failing side: observed at step 6.

## Not done
none

## Unverified
That the laptop's code page is CP1252; the message ('charmap', byte
0x81) matches it, but run the locale probe there to confirm.

## Decided for you
Did not set PYTHONUTF8 in CI or on the laptop: it would hide the
dependency, not remove it.
```
