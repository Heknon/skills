# Handoff

**Verdict you produce:** which skill owns the next step, and what you
give it.

```
owner:   <this skill | pytest | deployment | observability | git | navigation | packaging | offline-docs | pydantic | api | mongodb | architecture>
because: <the row below that matched>
give:    <what it needs from you: the traceback, the reproduction, the commit range>
```

This skill owns the generic loop: reproduce, shrink, one hypothesis at
a time, fix, prove. Other skills own their domain's ladder. Enter theirs
when the symptom is theirs; come back when they hand a Python bug over.

## Who owns what

| Situation | Owner | What passes between |
| --- | --- | --- |
| a failing test: reading its output, the phase, whether the test or the code is wrong | pytest (`core/read-failure.md`, `core/test-or-code.md`) | pytest hands over when the code is wrong and the cause is not in the output; this skill hands back for the regression test (`core/write-test.md`) |
| a test that fails only with others, in another order, with a seed, under xdist | pytest (`core/flaky-and-slow.md`) | a race inside the code under test comes here (`core/intermittent.md`) |
| a pipeline, job, image build, release or pod that fails | deployment (`core/debug.md`, its thirteen-hop ladder) | deployment hands over at "the container crashes with a Python traceback"; a cause in deployed configuration goes back |
| telemetry missing, wrong or duplicated; querying the backend | observability | a production trace or log line is evidence for a reproduction here; finding it is observability's. Logging here is only a temporary probe (`tools/logging.md`) |
| the hypothesis loop itself, reading the first error, breaking a loop | seniority (`core/hypothesis-loop.md`, `core/reading-errors.md`, `core/loop-breaker.md`) | this skill adds reproduction, shrinking, proof, and the Python and tool facts |
| which interpreter and packages run; finding code; reading history (`log -S`, blame) | navigation (`core/environment.md`, `core/history.md`) | `core/differ.md` uses its Environment answer |
| what a library function expects, from its installed source | offline-docs | when the raising frame is in a library, and to settle what a library's error means (`core/understand-error.md`, step 6) |
| what a library's error means in its domain: a `ValidationError`, an HTTP status, a `DuplicateKeyError`, an `IntegrityError` | pydantic (`core/read-error.md`), api (`core/methods-and-status.md`), mongodb, architecture (`sqlalchemy/errors.md`) | this skill reads the error's shape, prints the value and says what leaks (`python/exceptions.md`); the owner says what it means and how to handle it |
| a new exception class when an error is improved: when one is earned, where it lives, its fields | architecture (`placement/custom-errors.md`) | `core/improve-the-error.md` says what the error must name and who catches it |
| how and where errors are logged in production, and at which level | observability (`logs/levels.md`) | an Improve only keeps the traceback (`logger.exception`, `exc_info=True`) |
| bisect mechanics: start, good, bad, skip, `bisect run`, reset | git (`core/bisect.md`) | this skill gives it the good and bad versions and the repro script (`core/regression.md`) |
| why two machines resolved different package versions | packaging | this skill only shows the skew |
| slowness that is not a hang; production latency | out of scope here; production latency is observability's | |

## Steps

1. **Match the situation** to a row. If the first thing you have is a
   test failure, a job log or a dashboard, start in that skill.
2. **Give the owner what the row names**, copied, not described.
3. **Take back what comes back**: a Python traceback from deployment, a
   code bug from pytest, a commit from git. Continue in `core/loop.md`
   at the step it belongs to.

## Never

- Never repeat another skill's procedure from memory here; load it.
- Never keep going in this loop on a CI configuration, a chart or a
  dashboard problem: that ladder is another skill's.
