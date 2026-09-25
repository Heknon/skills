# Hypothesis loop

**Verdict you produce:** the confirmed cause and the step that confirmed
it, or every cause ruled out and what is left:

```
verdict hypothesis-loop: H<n> confirmed at step <m>: <cause>
verdict hypothesis-loop: all ruled out: <H list>; left: <what is still unexplained>
```

The first explanation that fits is usually not the only one. Weak
reasoning stops there. This loop forces a second candidate, a test that
could fail, and one change at a time.

## The loop

1. **Write the symptom exactly.** What was seen, where, when, copied, not
   interpreted. "exit 1, `KeyError: 'region'` at `loader.py:88`", not "the
   loader is broken".
2. **Reproduce it.** Run the thing that fails and see it fail. If it does
   not fail for you, that is the first finding: the hypotheses are now
   about what differs between your run and the failing one.
3. **Write at least two causes.** Always two or more. If you can think of
   only one, the second is "something in the environment differs", which is
   often true.
4. **For each cause, write a test and what disproves it.** The test is the
   cheapest observation that tells the causes apart. "Disproved if" is what
   you would see if the cause is wrong. If you cannot say what would
   disprove it, it is not a hypothesis yet; make it concrete.
5. **Pick the next test.** The one that is cheapest and decisive first,
   even if its cause is less likely. A test that separates two causes at
   once beats one that checks one.
6. **Run exactly one test. Change nothing else.** Record the step, then
   mark the hypothesis `confirmed at step <n>`, `ruled out at step <n>`, or
   leave it `open` if the test did not decide.
7. **Confirmed means both**: what the cause predicted happened, and what
   the other open causes predicted did not.
8. **Then fix, then rerun the reproduction from step 2.** The symptom must
   be gone in the same reproduction. If it was intermittent, run it as many
   times as it took to fail before, and say how many.

Write each hypothesis in your notes in this form:

```
- H1 [open] <cause> | test: <observation> | disproved if: <what you would see>
```

## Ways to find the cause faster

- **Compare**: find a case that works and one that fails. List every
  difference. The cause is among them.
- **Bisect**: halve the input, the config, or the commit range, and see
  which half fails. Repeat.
- **Minimise**: remove parts until it stops failing. The last part removed
  is involved.
- **Print at the boundary**: log the value where it enters the failing
  function. Wrong on entry means the cause is upstream.

## Never

- Never change two things between runs. When the symptom changes, you will
  not know which one did it.
- Never make a change that does not test a written hypothesis.
- Never declare a cause because one fix made one failure disappear once.
- Never throw away an observation that does not fit. It is a new
  hypothesis.
- Never raise a timeout or a retry count as a fix unless the confirmed
  cause is that the operation is slow and correct.

## Stop and ask

- Every hypothesis is ruled out and you cannot write a new one from the
  observations. Report the symptom, what each test showed, and what is left
  (`core/asking.md`).
- Reproducing needs access or data you do not have.
