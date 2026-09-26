# Inspect

**Verdict you produce:** what the program did at one point, seen at
runtime, and the probe gone again.

```
question: <what you need to see: "the keys of row when report.py:5 runs">
probe:    <the tool and where it was placed: "marked stderr print at report.py:5">
output:   <the lines it printed, copied>
answers:  <which hypothesis this confirms or rules out>
removed:  <the search that found no marker left: "git grep -n -I --untracked DBG: nothing">
```

There is no debugger window. Every look inside a running program is a
command that runs to the end and prints. Choose the probe that answers
the question with the fewest edits, and place it at a boundary.

## Choose the probe

| Question | Probe | Edits the code |
| --- | --- | --- |
| what does this function return for this input | call it: `uv run python -c "from m import f; print(repr(f(x)))"` | no |
| what were the local variables when it raised | `uv run python recipes/locals_on_error.py -m pkg ...` | no |
| what exception was hidden by `from None` | print `exc.__context__` (`tools/probes.md`) or `locals_on_error.py` | no |
| what is this value at this line | a marked print to stderr (`tools/probes.md`) | yes |
| how did the program get here | `traceback.print_stack(file=sys.stderr)` at that line | yes |
| what does this module already log at debug level | turn on one logger (`tools/logging.md`) | no, or one line |
| where is each thread now | a stack dump (`tools/faulthandler.md`) | no |
| what allocated the memory | `tracemalloc` (`tools/tracemalloc.md`) | no |
| step through the code | scripted pdb only (`tools/pdb.md`); usually a print is quicker | no |

Start from the top rows: a probe that needs no edit leaves nothing to
remove.

## Place it at a boundary

A boundary is where data passes from one part to another: the start of
a function (its arguments), a return, right after a file is read or a
message is taken off a queue. A wrong value seen at a boundary splits
the code in two: wrong on entry means the cause is upstream; right on
entry and wrong on exit means it is inside.

*lab (missing-key):* one print at the start of the loop in
`report.py` split parser from report:

```
DBG report keys: ['amount', 'customer', '﻿region']
```

The keys were already wrong on entry, so the cause was in the parser.

## Steps

1. **Write the question** and what each answer would mean for the open
   hypotheses, before placing anything.
2. **Pick the first probe in the table that answers it.**
3. **Mark every probe edit** with the same word, `DBG`, in the printed
   text and in a comment, so one search finds them all.
4. **Run the reproduction once** with the probe. Copy the output.
5. **Remove the probe** and search for the marker:

   ```powershell
   git grep -n -I --untracked DBG
   ```

   *lab:* `git grep` without `--untracked` found nothing in a file git
   did not track yet; with it, and `-I` to skip `.pyc` files, it found
   the probe. Outside git, see `tools/powershell.md`. Nothing may be
   found at the end.

## Never

- Never leave a probe, a `breakpoint()`, a raised log level or a `sleep`
  in the diff.
- Never place a probe where it changes timing when the bug is a race;
  it can hide the race (`core/intermittent.md`).
- Never print a secret to see it; print its length or whether it is set.
