# Recipes

## review_diff.py

A read-only helper for the steps a weak model gets wrong by eye: sizing
a diff, spotting a repeated edit, listing changed contracts, and
telling new tool lines from old ones. Standard library only; it runs
with the project's interpreter and changes no file.

```powershell
git diff --output=$env:TEMP\review.diff origin/main...HEAD
uv run --no-sync python <skill>\recipes\review_diff.py scope $env:TEMP\review.diff
uv run --no-sync python <skill>\recipes\review_diff.py defs $env:TEMP\review.diff
uv run --no-sync python <skill>\recipes\review_diff.py signs $env:TEMP\review.diff
uv run --no-sync python <skill>\recipes\review_diff.py newerrors $env:TEMP\base-ruff.txt $env:TEMP\head-ruff.txt
```

| Command | Prints (*lab*) | Used in |
| --- | --- | --- |
| `scope` | `13 files, +26 -26`; files with their own edit, largest first; `same edit in 12 files (digits read as N):` with the edit | `core/scope.md` |
| `defs` | per changed function: `return annotation: Book -> Book \| None`, `no longer raises: BookNotFound`, `moved from ...`, `parameters: (...) -> (...)`, `renamed to format_date?`, `fields: +rating: float`, module names removed; `test removed:` lines | `core/callers.md` |
| `signs` | `path:line  ID  text` for each line matching a `## Signs` pattern in `checklists/*.md`; removed lines say so and use the old numbering | `core/checklist.md` |
| `newerrors` | the ruff (`--output-format concise`) and mypy lines of the second file that the first lacks, compared without line and column | `core/tools.md` |

What it reads and how it fails:

- The diff file may be UTF-8, UTF-8 with a byte order mark, UTF-16
  (PowerShell 5.1 `>`), or CRLF; all four were read in the lab. Text
  before the first `diff --git` (a mail header, a commit message) is
  skipped.
- `defs` reads the old version of each file with `git cat-file -p
  <blob>` from the diff's `index` lines, so run it inside the
  repository. A blob that is not there prints `not read: <path>`;
  fetch the base and run it again. The new version is rebuilt from the
  old one and the hunks, so the head need not be checked out.
- A sign is a regular expression kept in the checklist it belongs to;
  `TST` signs read test files, the others read the rest. A pattern
  that no longer compiles stops the command with Python's `re.error`.
- Exit code 2 with the usage text for a wrong command; 2 with `no file
  diffs found` for a file that is not a unified diff.

Checked in the lab: ruff 0.16.9 (`E`, `F`, `B`, `I`, `UP`) and mypy
2.3.1 report nothing on it; run on fourteen seeded changes and a
separate lab service, including a 40-file change, a moved function, a
rename, a patch file with a mail header, and a UTF-16 copy.
