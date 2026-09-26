# Shrink

**Verdict you produce:** the smallest case that still fails the same way,
and what was removed.

```
minimal case: <the input, config and call that remain>
removed:      <what went, each checked: "rows 2 to 3: still fails", "the BOM: passes">
last removal that made it pass: <this is involved in the cause>
command:      <the reproduction on the minimal case, and its result>
```

A large failing case has many possible causes. Each part removed while
the failure stays is one cause ruled out. The part whose removal makes
the failure go is involved in the cause.

## Steps

1. **Keep the original.** Copy the failing input and work on the copy;
   the reproduction must still fail on the original at the end.
2. **Halve, run, keep the failing half.** For input: half the rows, half
   the records, half the keys. For configuration: half the settings back
   to their defaults. For code: call the inner function directly instead
   of the whole program. Run the reproduction after every cut.
3. **If both halves pass**, the failure needs something from each: go
   back one step and remove smaller pieces, one at a time.
4. **Stop when every remaining piece matters**: removing any one of
   them makes the reproduction pass. Write the last removal that made
   it pass; it points at the cause.
5. **Check it fails the same way**: the same exception, message and
   line as the original. A shrink that fails differently has found
   another bug; note it, and go back.

## Edit files by bytes, not by text

A tool that reads and writes text can change the bytes that cause the
bug. *lab (PowerShell 7.4 on Linux, not run on Windows):*

```powershell
Get-Content data/may.csv | Select-Object -First 2 | Set-Content small.csv
uv run python -m sales small.csv     # North 99.00, exit 0: the bug is gone
```

`Set-Content` wrote the file without the UTF-8 byte order mark that
caused the `KeyError`, so the shrunk case passed. Cut files with Python,
in binary:

```powershell
uv run python -c "l = open('data/may.csv', 'rb').read().splitlines(keepends=True); open('small.csv', 'wb').write(b''.join(l[:2]))"
uv run python -m sales small.csv     # KeyError: 'region', as before
```

The same holds for line endings, trailing spaces and tabs: when the
bug may live in the bytes, cut the bytes.

## Check the first bytes

When a text input behaves oddly, print its start as bytes before
anything else:

```powershell
uv run python -c "print(open('data/may.csv', 'rb').read(26))"
```

*lab:* `b'\xef\xbb\xbfregion,customer,amount\n'`: the three bytes before
`region` are the UTF-8 byte order mark, which some programs write at
the start of a file and `encoding="utf-8"` keeps as the character
`'﻿'`.

## Never

- Never shrink by editing the original input or the project's code in
  place; work on copies and keep the original failing.
- Never remove two pieces in one step: when the failure goes, you will
  not know which one mattered.
- Never stop at a case that fails with a different message.
