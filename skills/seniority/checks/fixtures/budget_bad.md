# Ledger

goal: "what does the --strict flag of build.py do?"
kind: answer
done when: the flag's effect named, with the line in build.py that reads it
budget: 3 steps
scope out: none

## Assumptions

none

## Hypotheses

none

## Steps

1. action: search "--strict" in build.py | result: build.py:14 add_argument | new fact: the flag is defined at line 14
2. action: search "args.strict" in build.py | result: build.py:88 | new fact: it is read at line 88
3. action: read build.py lines 80-100 | result: strict turns warnings into errors | new fact: strict makes warnings fatal
4. action: read build.py lines 100-140 | result: unrelated | new fact: nothing more about strict

## Done

observed at step 3: build.py line 88 makes every warning an error when --strict is set
