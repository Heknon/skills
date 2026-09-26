# Windows and PowerShell

What differs for a refactoring on Windows. Git's own Windows facts
(line endings, quoting, paths, case) are the git skill's
`reference/windows.md`; this page adds only what touches a step.
Commands marked *PowerShell 7.5 on Linux* ran there; nothing here ran on
Windows itself.

| Situation | What happens | Do |
| --- | --- | --- |
| `stash@{0}` unquoted in PowerShell | `Too many revisions specified: 'stash@' 'MAA=' 'xml' 'xml'` (*PowerShell 7.5 on Linux*): the braces are a script block | quote it: `git stash show --include-untracked --stat 'stash@{0}'` |
| a case-only rename of a module (`Reports.py` to `reports.py`) | the file system ignores case; Python's finder does not unless `PYTHONCASEOK` is set (`importlib/_bootstrap_external.py`, 3.12 source), so an import spelled with the other case fails; renaming in Explorer or the editor may not be recorded by git | `git mv` the file, and search the imports for both spellings; `not run on Windows` |
| an edit writes LF into a file stored with CRLF, or the reverse | `git diff --stat` shows every line of the file changed, which buries the step | stop; the git skill's `core/clean-up.md`; never commit a whole-file ending change inside a step |
| saving probe or names output | `Out-File -Encoding utf8` writes UTF-8 without a byte order mark in PowerShell 7 (*PowerShell 7.5 on Linux*), with one in Windows PowerShell 5.1 (`not run on Windows`) | write both files of a comparison the same way; `git diff --no-index` compares them as text either way |
| a probe printing characters outside a code page such as CP1252 | with the output encoding forced to `cp1252` (`PYTHONIOENCODING=cp1252`, standing in for a Windows console), printing `→` raised `UnicodeEncodeError: 'charmap' codec can't encode character '→' in position 0: character maps to <undefined>`; `PYTHONIOENCODING=utf-8` printed it | set `$env:PYTHONIOENCODING = "utf-8"` before running the probe; the debugging skill's `python/encoding.md` for the rest |
| `mkdir app/reports` | works in PowerShell (*PowerShell 7.5 on Linux*); `git mv` then moves the file into it | as in `steps/split-module.md` |
| `PYTHONDONTWRITEBYTECODE` for a break-and-restore loop | `$env:PYTHONDONTWRITEBYTECODE = "1"` lasts for the session | `legacy/characterization.md` |
| paths in patch targets and dotted config | always dots: `"app.reports.clock.now"`, never backslashes | |
| searching in the terminal | `git grep -n -w -I <name>` behaves the same in PowerShell; `Select-String` is case-insensitive unless given `-CaseSensitive` (navigation's `tools/zed-tools.md`) | prefer the editor's `grep`, then `git grep` |
