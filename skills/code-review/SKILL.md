---
name: code-review
description: Review Python backend code and say whether it can merge. Review a branch, a patch file or a GitLab merge request, a whole module, the tests in a change, a security pass, or a re-review after the author's fixes. Scope and size the diff, read the callers of every changed signature, return, raise and default, run the project's own ruff, mypy and pytest on the change and its base and report only new errors, walk the checklists (correctness, errors, edge cases, concurrency, security, tests, API contract, data, models, layering L1 to L11), rank each finding blocker, major, minor or nit by its failure scenario, and end in one verdict - approve, approve with comments, changes needed, cannot judge. Task words - review, code review, CR, MR, merge request, PR, pull request, LGTM, look over, check my change, second pair of eyes, re-review, can this merge, is this safe. Verified on git 2.43.0, Python 3.12, ruff 0.16.9, mypy 2.3.1, pytest 9.1.1, FastAPI 0.141.1, pydantic 2.13.5, PyMongo 4.18.2, MongoDB 8.0.32.
---

# Code review

This skill knows how to review a change and decide whether it can
merge. Every command, output and behaviour in it was run in a lab on
git 2.43.0, Python 3.12.14, ruff 0.16.9, mypy 2.3.1, pytest 9.1.1,
FastAPI 0.141.1, pydantic 2.13.5, Beanie 2.2.0, PyMongo 4.18.2 and
MongoDB 8.0.32, or read in installed source; GitLab calls were read in
python-gitlab 8.5.0 and are marked *not run*. Nothing is written from
memory, and nothing in a review may be: a finding rests on a run, a
read line, or an inference you label as one.

Read this file, then load only what the task needs.

## Read the versions first

In the repository under review:

```
git --version
uv run --no-sync ruff --version
uv run --no-sync mypy --version
uv run --no-sync pytest --version
uv pip show fastapi pydantic beanie pymongo
```

The project's versions decide what its tools report and which facts
from other skills apply. A package shown as not found is not used.

## The kinds of task

| Kind | You were asked to | Load |
| --- | --- | --- |
| **Diff** | review a branch, a patch or a merge request; "can this merge", "LGTM?" | `core/scope.md` and the `sources/` file for where it lives, then `core/tools.md`, `core/callers.md`, `core/checklist.md`, `core/rank.md`, `core/verdict.md` |
| **Module** | review a module or package, with no diff | the same as Diff; `core/scope.md` step 7 sets the scope |
| **Re-review** | review again after the author's fixes | `core/re-review.md`, then Diff's files for the fix |
| **Tests** | review the tests, or the tests in a change | `core/review-tests.md`, `checklists/tests.md` |
| **Security** | a security pass over a change or a module | `core/security-pass.md`, `checklists/security.md` |

A Diff runs in this order: scope, tools, callers, checklists, rank,
verdict, then the answer in `output/format.md`.

## Where the facts are

| Folder | Holds |
| --- | --- |
| `core/` | the procedures above; each ends in a verdict line |
| `checklists/` | one file per pass: each item a question, a sign in a diff, a failure scenario, a default severity, and the skill that owns the facts; `## Signs` blocks feed the recipe |
| `sources/` | getting the change: `git-diff.md` (a branch), `patch-file.md`, `gitlab-mr.md` (*not run*) |
| `output/` | `format.md`: the answer, the finding, the four headings |
| `recipes/` | `review_diff.py`: `scope` (sizes, repeated edits), `defs` (changed contracts), `signs` (checklist leads), `newerrors` (tool lines the base lacks); `README.md` |
| `examples/` | three finished reviews: a diff (`review-a-diff.md`), a re-review after a rebase (`re-review.md`), a tests review (`review-tests.md`) |

`glossary.md` fixes the words. Other skills own the facts behind many
checklist items; the item names the file. architecture: layering IDs
L1 to L11 and the structure card. linting: what a tool line means, and
running tools as CI does. pydantic, api, mongodb: models, the HTTP
contract, queries and writes. navigation: finding callers (Trace in)
and following a value (Follow). offline-docs: what an installed
library really does. git: commits and their messages. debugging: the
reproduction template. refactoring: every restructuring. pytest:
whether a test can fail. deployment: GitLab access. Seniority's habits
apply to every step; this skill does not restate them.

## Invariants

1. **A finding names a `path:line` and a failure scenario**: the input
   or state, and the wrong result. No line: not reported. No scenario:
   at most a nit.
2. **Severity comes from the scenario**, never from the topic or the
   tone asked for (`core/rank.md`). Nits: at most five, grouped, last.
3. **Run before you judge.** The project's tools and tests run on the
   change. Never `approve` when nothing ran.
4. **Read the callers** of every changed signature, default, return
   and raise. A change is judged by what relies on it.
5. **Tool output is reported once, under Checked.** It is never
   retold as a finding; a finding on a flagged line adds a scenario.
6. **A claim about a library is settled in the installed source**
   (offline-docs), never from memory of another version.
7. **The diff decides, not the description.** "No behaviour change" is
   a claim to check.
8. **Review, do not rewrite.** No edits to the code under review; the
   smallest fix goes in `suggest:`, a restructuring is named for the
   refactoring skill. Reproductions live outside the repository and
   are deleted; a deliberate break is restored and `git status` is
   clean again.
9. **Every review ends in one verdict** and says what was not
   reviewed.
10. **Nothing goes to GitLab unless asked**; then the text is shown
    first and posted as one note.
11. **Domain facts come from their owner.** A checklist item asks the
    question; the named skill, a run or the installed source answers.

## What you say when you finish

End with these headings, in this order, each with `none` when empty
(`output/format.md` has the full shape). If another skill is loaded,
its headings come first and these after; seniority's come last.

```
## Verdict
<approve | approve with comments | changes needed | cannot judge>: <reason>

## Findings
<numbered findings, blockers first; nits grouped; then "seen before this change">

## Checked
<reviewed head and base; each tool, test run, caller search and case run, with its summary line>

## Not reviewed
<files not read line by line, what could not run, callers not searched>
```

The `evals/` folder is for people testing this skill. Never open it
while doing a task.
