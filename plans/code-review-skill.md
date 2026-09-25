# Plan: the code-review skill

Status: draft for decision. Nothing is built yet.

## 1. What it is

A procedure for reviewing Python backend code and saying whether it can
be merged. It scopes the change, reads the code that calls it, runs the
project's own tools, walks checklists, ranks what it found by severity,
and ends in a verdict. Every finding names a line and a failure scenario:
the input or state, and the wrong result it leads to. A finding without
a line is not reported; one without a scenario is at most a nit.

It owns the procedure, the ranking and the verdict; other skills own
the facts behind many checklist items (section 6). It carries judgement,
not enforcement. Seniority's habits (evidence outranks memory, challenge
before concluding) apply to each finding; this skill does not restate
them.

## 2. The environment it is written for

- **A weak model** (MiniMax 2.7 for evals) in Zed's agent on Windows,
  PowerShell, air gapped, no web. Python runs through uv; tools are
  whatever the project already has (`uv run --no-sync ruff check`,
  `mypy`, `pyright`, `pytest`). Nothing is installed to review.
- **Self-managed GitLab.** Changes arrive as merge requests. No review
  bot or GitLab MCP server is assumed.
- **Three sources for the change**, one file each in `sources/`:
  `git diff` against the merge base (`main...HEAD`, `--stat` first); a
  patch file, read as text or checked with `git apply --check`; a GitLab
  MR through the REST API (token and CA as in deployment's
  `gitlab/api.md`): its `diff_refs`, its diffs, its head fetched into a
  checkout. Endpoints, paging and truncation to verify in the lab.
- **Windows traps**, to verify in the lab: PowerShell 5.1 `>` writes
  UTF-16 (use `git diff --output=<file>`); `core.autocrlf` can turn one
  changed line into a whole-file diff.

## 3. The kinds of task

| Kind | Asked to | Answer shape |
| --- | --- | --- |
| **Diff** | review a change: a branch, a patch, an MR | verdict, ranked findings, what was checked, what was not reviewed |
| **Module** | review a whole module or package, no diff | the same, with the module's public surface as the scope instead of changed lines |
| **Re-review** | review again after fixes | each earlier finding marked fixed, not fixed or disputed; new findings from the fix only; a new verdict |
| **Tests** | review tests, or the tests in a change | per test: can it fail, what it misses; untested changed behaviour listed |
| **Security** | a security pass over a change or module | findings each with the input that exploits it; `none found` names what was searched |

## 4. The failures it targets

| Failure | What it looks like |
| --- | --- |
| **Nit wall** | twenty remarks on names and spacing; the off-by-one in the loop is not among them |
| **Unanchored finding** | "error handling could be improved", with no `path:line` and no input that goes wrong |
| **Tool echo** | restating what ruff or mypy already flag, in prose, as the reviewer's own insight |
| **Diff tunnel vision** | only the changed lines read; the caller that relied on the old return value or exception breaks unseen |
| **Unrun LGTM** | "looks good" with no tool, test or search run |
| **Remembered API** | "this misuses `X`", from memory of another version; the installed source says otherwise |
| **Severity inflation** | a naming issue marked critical; everything "must fix"; the one real blocker lost in the noise |
| **No verdict** | a list of remarks and no answer to "can this merge" |
| **Trusting the description** | the MR says "no behaviour change" and the review believes it instead of the diff |
| **Rewrite as review** | a redesign proposed, or performed, where a two-line fix was the finding |

## 5. Layout

```
skills/code-review/
  SKILL.md           router over the five kinds, invariants, answer shape
  glossary.md        finding, failure scenario, severity, verdict, scope
  core/
    scope.md         get the change, size it, name what is in and out
    callers.md       who relies on each changed signature, return, raise
                     or default (navigation's Trace in)
    tools.md         run what the project configures; new errors only
    checklist.md     which checklists the change calls for, one pass each
    rank.md          the severity scale, decided by the failure scenario
    verdict.md       the verdict from findings and from what was not run
    re-review.md     match earlier findings to the fix diff
    review-tests.md  untested behaviour; points at pytest for the rest
    security-pass.md outside input traced to where it is used
  checklists/        each item: question, sign in a diff, failure
                     scenario, default severity, owning skill
    correctness.md   logic, off-by-one, wrong variable, inverted test
    errors.md        swallowed exceptions, broad except, wrong status
    edge-cases.md    empty, None, zero, duplicates, unicode, time zones
    concurrency.md   blocking call in async, read-modify-write races
    security.md      injection (Mongo operators too), secrets, authz
    tests.md         behaviour with no test, tests that cannot fail
    api-contract.md  response shape, status codes, PATCH (see api)
    data.md          queries, indexes, unbounded reads (see mongodb)
    models.md        validators, defaults, unset vs None (see pydantic)
    architecture.md  from the architecture skill: a route that queries
                     the DB directly, business logic in a router, a DB
                     model returned in a response, a service importing
                     FastAPI, a transaction split across layers
  sources/           git-diff.md, patch-file.md, gitlab-mr.md
  output/format.md   the finding shape, the severities, the verdict
  examples/          three finished reviews: a diff, a re-review, tests
  evals/evals.json   sandboxes, one bait each
```

The answer, fixed in `output/format.md`: `## Verdict` (one of CR2, with
its reason), `## Findings`, `## Checked` (each tool, test and caller
search, with its summary line), `## Not reviewed`. One finding:

```
[1 blocker] app/orders/service.py:42
  when: <input or state> -> <wrong result>
  evidence: ran <command> | read <path:line> | inferred
  suggest: <smallest fix, or a refactoring named for later>
```

## 6. Dependencies and boundaries

From the roadmap, section 3:

| Skill | Needs | Relies on by name | Existing skills it touches |
| --- | --- | --- | --- |
| code-review | architecture, linting | architecture, linting, pydantic, api, mongodb | pytest, seniority |

- **architecture (needs).** It owns the layering rules.
  `checklists/architecture.md` turns each into an item with a sign in a
  diff and a default severity, and cites the rule; it never restates why.
- **linting (needs).** It owns what ruff, mypy and pyright catch. The
  review runs the project's configured tools, lists new errors once
  under *Checked*, and lets them weigh on the verdict; it never retells
  a tool's message as its own finding.
- **pydantic, api, mongodb (by name).** They own the domain facts (unset
  vs `None`, PUT vs PATCH, response models, indexes). Their checklists
  ask the question and send the model to the owner for the answer.
- **refactoring (boundary).** It owns the change procedure. A finding
  may suggest a restructuring by name; the review never performs it.
- **pytest (touches).** It owns whether a test can fail
  (`core/write-test.md`); the review adds changed behaviour with no test.
- **seniority (touches).** Its evidence levels label each `evidence:`
  line; its Challenge moment is applied to each blocker and major.

### Proposed changes to the roadmap

- **navigation under "Existing skills it touches".** Reading callers
  is its Trace in question; `core/callers.md` relies on it by name.
- **offline-docs under "Relies on by name".** Only the installed source
  answers the remembered-API failure, and offline-docs owns that.
- **git: make the table agree with the build order.** Section 4 says
  code-review stands on git; the table omits it. Proposed: git under
  "Relies on by name" (fetching an MR head, the merge base), not "Needs".
- **deployment under "Existing skills it touches", with a boundary
  row:** deployment owns the GitLab API (tokens, CA, PowerShell calls);
  code-review owns only the MR diff and note endpoints it uses.

## 7. How it will be verified

- **A sample service**: FastAPI, pydantic, Beanie on MongoDB, tests,
  ruff and mypy, on the R2 versions and the linting plan's tool pins;
  shared with architecture's sample if it has one (to verify in the lab).
- **Seeded diffs**, each with one known bug at a known line, plus clean
  diffs. Each bug is proven by a test that fails with the diff applied.
- **Every command in `sources/` and `core/tools.md`** on PowerShell 5.1
  and 7; the MR endpoints on deployment's GitLab CE 19.4 lab, including
  a diff large enough to be truncated.
- **Measured on the weak model:** recall (seeded bugs found at the right
  line, severity within one level); false positives (findings a person
  judges wrong; any blocker or major on a clean diff); noise (nits and
  tool echoes per review); verdict accuracy. Targets follow a baseline
  run (CR6).

## 8. Evals, written first

Each sandbox is a repository with a diff, patch or recorded MR response.

| # | Sandbox | Bait | Passes when |
| --- | --- | --- | --- |
| 1 | pagination off-by-one in a diff full of ugly names | nit wall | blocker found at its line; nits grouped, at most five |
| 2 | a function now returns `None` instead of raising; its caller is outside the diff | diff tunnel vision | the caller's `path:line` is named with the scenario |
| 3 | ruff and mypy each flag one issue; one logic bug neither sees | tool echo | tools run and summarised; the logic bug is the finding |
| 4 | a correct, clean change | false positive, unrun LGTM | tools and tests run; `approve`; no blocker or major |
| 5 | a library call correct on the pinned version, wrong in an older one | remembered API | installed source read before any claim; no false finding |
| 6 | a route passes request JSON into a Mongo filter | security | blocker with an input such as `{"$ne": null}` |
| 7 | a route queries Beanie directly and returns the document with `password_hash` | layering, leak | leak ranked above layering; refactoring suggested, not done |
| 8 | a new test asserts on its own mock | test that cannot fail | says so; ideally breaks the code to show it still passes |
| 9 | re-review: three findings, two fixed, the fix adds a new bug | re-review | each old finding marked; the new bug found; fixed ones not re-raised |
| 10 | read, modify, `save` on a counter under concurrent requests | concurrency | major, with the interleaving that loses an update |
| 11 | only a missing docstring and a long name | severity inflation | `approve with comments`; no blocker |
| 12 | MR description says "no behaviour change"; a default changed | trusting the description | the changed default is a finding |
| 13 | `except Exception: pass` around a write, route returns 200 | errors | major, with the failed write that reports success |
| 14 | forty files changed | scope | `--stat` first; what was not reviewed is listed, not skimmed |

## 9. Decisions needed

### CR1. Severity scale

*Recommended:* four levels, set by the failure scenario. **Blocker**:
wrong data, a security hole, a crash on a normal input. **Major**: wrong
behaviour on a plausible input, a broken contract. **Minor**: an
unlikely failure, a layering breach with no failure yet. **Nit**: taste.
A finding without a scenario can only be a nit.

### CR2. Verdicts

*Recommended:* `approve`, `approve with comments` (minors and nits
only), `changes needed` (any blocker or major, or a new tool error the
CI runs), `cannot judge` (the diff is incomplete, or tests could not
run and the change needs them). Never `approve` when nothing was run.

### CR3. May it post comments to GitLab?

*Recommended:* only when asked; posting is outward facing (seniority
invariant 6). Then one MR note, text shown first; line discussions only
if they work on 19.4 (to verify in the lab).

### CR4. May it fix what it finds?

*Recommended:* no. A fix is a separate task; a finding may show the
smallest fix as text. It writes only throwaway reproductions (CR5).

### CR5. May it run code to prove a finding?

*Recommended:* yes, for blockers and majors: a failing test in a
temporary folder outside the repository, deleted after, its run
reported. Whether a weak model cleans up is to verify in the lab.

### CR6. Targets and caps

*Recommended:* nits capped at five, grouped. Targets set after the
baseline, aiming at every seeded blocker found and no blocker or major
on a clean diff.

### CR7. Which checklists run

*Recommended:* correctness, errors and edge cases always; the rest by
what the change touches (a route: api-contract, security, architecture;
a query: data; a model: models), one pass each. Compared in the lab with
one combined pass, since nine at once may cost a weak model recall.
