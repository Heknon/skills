# Regression

**Verdict you produce:** the first bad commit, found by running a
script, and the cause in its diff.

```
good:   <commit or tag> -> <repro script result there: "GOOD (0)">
bad:    <commit> -> <result: "BAD (1): ...">
script: <path, outside the repository, and its exit codes 0 / 1 / 125>
first bad commit: <hash and subject, from git's output>
cause:  <the line in that commit's diff, and why it gives the symptom>
```

When the bug was not there at an older version, a bisect finds the
commit that brought it in, with about log2(N) runs instead of N diffs
read. This skill owns deciding it is a regression, proving a good
commit, and the script. The git skill owns the bisect itself
(`core/bisect.md`): starting, marking, `bisect run`, the log and the
reset.

## Steps

1. **Is it a regression?** Someone says it worked before. Believe it
   only after running the reproduction at that version. If it fails
   there too, it is an old bug: go back to `core/loop.md`.
2. **Write the repro script** from `recipes/repro_template.py`:
   - exit 0 when the bug is absent, 1 when present;
   - exit 125 when this version cannot be tested: it does not import,
     or it fails in a way that is not the bug;
   - import the project inside the check, not at the top, so a broken
     version gives 125, not 1;
   - keep it **outside the repository** (for example the parent folder),
     so checking out old commits cannot change or delete it, and run it
     from the project root.
3. **Run the script at both ends before bisecting**: at the good version
   it must print `GOOD (0)`, at the bad one `BAD (1)`. A `SKIP (125)` at
   either end means the script is broken, not the code (*lab:* a script
   kept outside the project returned 125 everywhere until it put the
   current folder on `sys.path`; `core/reproduce.md`).
4. **Hand over to the git skill** for the bisect, with the good version,
   the bad version and the script. In the lab it ran as:

   ```powershell
   git bisect start HEAD v1.4
   git bisect run uv run python ..\repro_to_kg.py
   git bisect reset
   ```

   (git 2.43.0 on Linux; the PowerShell form is not run on Windows.)
5. **Read the first bad commit's diff** (`git show <hash>`; reading
   history is the navigation skill's). Find the changed line that
   explains the symptom, and check it with the repro script: the commit
   before is good, this one is bad.
6. **Back to `core/loop.md` step 6**: fix, and prove the fix with the
   same script.

## Why exit code 125 matters

*lab (regression sandbox, 27 commits after v1.4):* one commit,
"Start troy ounces", left `units/mass.py` with a syntax error, fixed in
the next commit; the regression came two commits later, in "Tidy
conversion helpers".

| Check used by `bisect run` | What bisect named |
| --- | --- |
| `uv run pytest -q tests/test_units.py::test_pounds_to_kg` (a collection error exits non-zero, so counts as bad) | `Start troy ounces`: wrong |
| the repro script, exiting 125 on `SyntaxError` | `Tidy conversion helpers`, after `# skip: ... Start troy ounces` in the log: right |

A check that cannot tell "the bug" from "anything else went wrong" names
the first commit that broke anything.

## Never

- Never read a long range of diffs and guess when a bisect can run.
- Never assume the good version is good; run the script there.
- Never bisect with a check that exits 1 for an import or syntax error.
- Never leave a bisect running: `git bisect reset`, and the branch you
  started on is checked out again.
