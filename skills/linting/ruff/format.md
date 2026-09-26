# ruff format, and moving from black

**What it decides:** how to format code with ruff, what differs from
black, and how to check formatting like CI. Verified on ruff 0.16.9
against black 26.5.1.

## Commands

| Command | Does | Result in the lab |
| --- | --- | --- |
| `ruff format --check <paths>` | reports, writes nothing | exit 1 and `N files would be reformatted`; on 0.16.9 it also printed each file's change |
| `ruff format --diff <paths>` | prints the diff, writes nothing | exit 1 when there is a diff |
| `ruff format <file>` | formats | `1 file reformatted` |
| `ruff format --range 4-8 <file>` | formats only those lines, end exclusive; one file only | used to format one function in an unformatted file |

CI usually runs `ruff format --check .`; run the same.

## ruff format against black

One sample file, formatted by each (black with `--target-version py312`
so both assumed the same Python). Everything else was identical.

| Construct | black 26.5.1 | ruff 0.16.9 |
| --- | --- | --- |
| implicit string concatenation that fits: `'hello ''world'` | kept as two strings, `"hello " "world"` | joined, `"hello world"` |
| the same with f-strings | kept as two | joined into one f-string |
| a blank line after `class A:` before the first method | kept (one blank line) | removed |
| a comment after an opening bracket, `x = [  # comment` | collapsed to `x = [1, 2]  # comment` | bracket kept open, one item per line with a trailing comma |

Without a target version, black also split a long two-item `with`
differently (it wrapped the call; ruff used parenthesised context
managers, which its default target version allows). Set the target
version for both when comparing.

## Moving a project from black to ruff format

1. Check the settings match: `line-length` (both default to 88), quote
   style (`format.quote-style`), `target-version`.
2. Run `uv run --no-sync ruff format --diff .` and read the size of the
   difference. It will contain the cases above.
3. Make the switch its own commit: config, dev group, pre-commit hook,
   and the reformat, with the reformat's hash in
   `.git-blame-ignore-revs` (the git skill makes it).
4. Remove black from the dev group and hooks in the same commit, so the
   two never fight in a hook loop (`pre-commit/blocked.md`).

## Line endings

`format.line-ending` defaults to `auto`: each file keeps the ending it
has, and a file with mixed endings gets its first one. `lf`, `cr-lf`
and `native` force one (`ruff config format.line-ending`). Windows
line endings and hooks: `pre-commit/windows.md`.

## Never

- Never format files the task did not touch (`core/in-scope.md`).
- Never mix formatter changes and logic changes in one commit.
