# Bisect

**Verdict you produce:** the first bad commit, the test that decided
each step, the log, and `bisect reset` done.

```
good:   <commit or tag> (checked: <how>)
bad:    <commit> (checked: <how>)
script: <path outside the repository>, exit 0 good, 1 bad, 125 skip
result: <hash> <subject> ("<hash> is the first bad commit")
skipped: <commits bisect could not test, from git bisect log>
verdict bisect: <found | range of candidates because of skips | stopped: <why>>
```

The debugging skill owns the investigation; it hands over here with a
known good and a known bad version. The pytest skill owns the test the
script runs.

## Steps

1. `git status`: clean, nothing in progress. Stash otherwise.
2. Confirm the ends by running the check yourself: at the bad commit it
   must fail, at the good one pass (`git switch --detach v1.0`, run,
   `git switch -` back). An end that is not what you think makes the
   answer wrong.
3. Write the test script **outside the repository**, or in a folder that
   no commit tracks: bisect checks out old commits. Start from
   `recipes/bisect_test.py` (Python, any platform), or
   `recipes/bisect-test.sh` / `.ps1` (runs one pytest file). Exit codes,
   from `builtin/bisect.c` in 2.43.0:
   | Exit | Means |
   | --- | --- |
   | 0 | good |
   | 1 to 127, except 125 | bad |
   | 125 | cannot test this commit: skip it |
   | 128 or more, or negative | bisect run stops with an error |
   A commit that does not import or build is **125**, never 1.
4. Run it:
   ```
   git bisect start <bad> <good>
   git bisect run uv run --no-project python ../bisect_test.py
   ```
   `git bisect start HEAD v1.0` printed `Bisecting: 19 revisions left to
   test after this (roughly 4 steps)`.
5. Read the result line: `2d373da... is the first bad commit`, then the
   commit. With skips next to the answer, bisect may give a range: `There
   are only 'skip'ped commits left to test. The first bad commit could
   be any of:` with the hashes, then `We cannot bisect more!` and
   `error: bisect run cannot continue any more` (lab). Report the range.
6. `git bisect log`: the steps, with `git bisect skip <hash>` lines for
   the untestable commits. Put it in the answer.
7. `git bisect reset`. It printed `Previous HEAD position was ...` and
   `Switched to branch 'main'`. Then `git status`: no bisect in
   progress. `git bisect reset -q` is not an option (`error: '-q' is not
   a valid commit`) and left the bisect running.

## By hand, when no script is possible

`git bisect start <bad> <good>`, then at each step check and say
`git bisect good`, `git bisect bad` or `git bisect skip`, until the first
bad commit line; then `git bisect reset`.

## What the lab showed

In the sandbox, seven commits in the middle could not import
`shop.money`. The first midpoint (`Update changelog (20)`) was one of
them. A script that let the `ModuleNotFoundError` exit 1 blamed `Pad
amounts in money helpers`, the commit that broke the import. The recipe,
exiting 125 there, skipped two commits and named `Use the context
rounding in to_cents`, the real change.
