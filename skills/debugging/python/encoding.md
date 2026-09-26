# Text encoding

**What it decides:** why the same file reads correctly on one machine
and fails or turns to nonsense on another, and how to show it.

## The default

`open(path)` in text mode without `encoding=` uses the locale's encoding
unless UTF-8 mode is on. Ask the interpreter that runs the code:

```powershell
uv run python -c "import locale, sys; print(locale.getencoding(), sys.flags.utf8_mode)"
```

| Machine | Printed in the lab |
| --- | --- |
| Linux, no locale set (the lab container, and the CI log in the utf8-ci sandbox) | `UTF-8 1`: Python switched to a UTF-8 locale and UTF-8 mode by itself |
| Linux, `LC_ALL=C.UTF-8` | `UTF-8 0`: UTF-8 mode off, but the locale is UTF-8 anyway |
| a CP1252 locale, standing in for a Windows machine | `CP1252 0` |
| the same, with `PYTHONUTF8=1` | `CP1252 1`: the locale is unchanged, but `open()` now uses UTF-8 |

Windows itself was not run: its code page comes from the machine's
language settings, so check it there with the command above.

## What a wrong encoding looks like

The file `data/customers.txt` holds `Álvaro Núñez` in UTF-8. *lab
(3.12.14, CP1252 locale):*

```
E       UnicodeDecodeError: 'charmap' codec can't decode byte 0x81 in position 1: character maps to <undefined>
```

`Á` is the two bytes `c3 81` in UTF-8; `0x81` has no character in
CP1252. Most other UTF-8 letters do decode, to the wrong characters
(`Ã©` for `é`), with no error: wrong values that travel on.

Other messages of the same family: `'ascii' codec can't decode byte
0xc3 in position 3: ordinal not in range(128)` (*lab:* an ASCII locale
with UTF-8 mode off).

## Show it, then fix it

1. **Flip UTF-8 mode on the failing side** (`core/differ.md`):

   ```powershell
   $env:PYTHONUTF8 = "1"
   uv run pytest -q          # passes
   Remove-Item Env:PYTHONUTF8
   uv run pytest -q          # fails again
   ```

   (*lab:* the same flip with a CP1252 locale on Linux: failed, passed,
   failed. The PowerShell lines are not run on Windows.)
2. **Find every call that relies on the default**, on either machine:

   ```powershell
   $env:PYTHONWARNDEFAULTENCODING = "1"
   uv run pytest -q
   ```

   *lab:* pytest's warnings summary showed
   `names/load.py:3: EncodingWarning: 'encoding' argument not specified`
   while the test still passed on the UTF-8 machine. `uv run python -X
   warn_default_encoding ...` does the same for a script.
3. **Fix the call**: `open(path, encoding="utf-8")`, and the same for
   `Path.read_text`, `Path.write_text` and `subprocess` with `text=True`
   where the data is UTF-8. A file that may start with a byte order mark
   needs `encoding="utf-8-sig"` (*lab, missing-key:* `utf-8` kept it as
   `'﻿'` at the start of the first column name).
4. **Prove it with UTF-8 mode off** on the failing side: *lab:* after
   the fix, `PYTHONUTF8=0` with the CP1252 locale: `1 passed`.

Setting `PYTHONUTF8=1` in CI or on a machine proves the cause; it is not
the fix, because the next machine will not have it.

## 3.15

On 3.15.0rc2 UTF-8 mode was on by default (`python/versions.md`).
