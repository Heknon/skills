# Glossary

One sentence per term. Use these words and no synonyms.

| Term | Meaning |
| --- | --- |
| change | What is under review: a branch against its target, a patch, or a merge request. |
| base | The commit the change starts from: the merge base of the branch and its target (`git merge-base`). |
| head | The last commit of the change, as reviewed; its hash goes under *Checked*. |
| diff | The change as text, from the base to the head (`git diff <target>...HEAD`, three dots). |
| scope | What the review reads line by line, what it reads as one repeated edit, and what it leaves out. |
| repeated edit | The same lines changed in many files (digits aside), read once and checked as a group. |
| contract | What callers of a function rely on: its parameters and defaults, return values, exceptions raised, and the meaning of each. |
| changed contract | A contract the change alters, listed by `review_diff.py defs` or found by reading. |
| caller | Code that calls, imports, catches or subclasses what the change touched, inside or outside the diff. |
| pass | One reading of the diff with one checklist's questions only. |
| sign | A pattern in a diff line that points at a checklist item; a lead, never a finding. |
| lead | A line worth opening; it becomes a finding or is set aside. |
| finding | A problem at a `path:line`, with a failure scenario, a severity, evidence and a suggestion. |
| failure scenario | An input or state, and the wrong result it leads to: `GET /books/b-2 (no ratings) -> 500`. |
| severity | blocker, major, minor or nit, decided by the failure scenario (`core/rank.md`). |
| blocker | Wrong or lost data, money or stock, a security hole, a crash or red CI on a normal input. |
| major | Wrong behaviour on a plausible input, a broken contract, a lost update under normal load. |
| minor | A failure that needs an unlikely input or a future change, a breach with no failure yet, a test gap. |
| nit | Taste: names, comments, style no tool enforces. |
| tool line | One line of ruff, mypy or pyright output; reported under *Checked*, not as a finding. |
| new tool line | A tool line on the head that the base does not have, compared without line numbers. |
| verdict | The one answer to "can this merge": approve, approve with comments, changes needed, cannot judge. |
| evidence label | `ran`, `read` or `inferred`: how a finding is known (seniority's observed, read, inferred). |
| reproduction | A throwaway script or test outside the repository that shows a finding, deleted after. |
| seen before this change | A problem in code the change does not touch; listed, not ranked, outside the verdict. |
| re-review | A review of the fix to earlier findings, marking each fixed, not fixed, disputed or moot. |
