# Ledger

goal: "Tidy up lib.py"
kind: change
done when: total() written more plainly, with every public name, parameter, default and result unchanged, shown by `python3 .ledger/probe.py` giving the same output before and after
budget: 15 steps
scope out: load() ignores its strict parameter

## Assumptions

- A1 [unverified] the person means readability only, no behaviour change

## Hypotheses

none

## Steps

1. action: read lib.py | result: two functions, load and total, 12 lines | new fact: total is one expression; load never reads strict
2. action: `cp lib.py .ledger/before/lib.py` | result: snapshot taken | new fact: the old lib.py is kept for the change check
3. action: write .ledger/probe.py calling total on four inputs | result: probe written | new fact: the probe covers an empty list, floats and a negative discount
4. action: edit lib.py total to name the subtotal | result: two lines instead of one | new fact: total now names its subtotal
5. action: `python3 .ledger/probe.py` | result: 6, 0, 3.0, 7 | new fact: the changed total gives the probe's four results

## Done

observed at step 5: the probe prints 6, 0, 3.0 and 7, and check_finish compares it with the old code
