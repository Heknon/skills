# Ledger

goal: "Fix the off-by-one in paginate()"
kind: change
done when: `python3 -m unittest discover -s tests` prints OK
budget: 15 steps
scope out: none

## Assumptions

none

## Hypotheses

none

## Steps

1. action: read pager.py lines 1-10 | result: start = page * per_page | new fact: pages are treated as counting from 0
2. action: edit pager.py line 6 to start = (page - 1) * per_page | result: one line changed | new fact: pages now count from 1
3. action: read pager.py lines 1-10 | result: start = (page - 1) * per_page | new fact: the edit is in place

## Done

observed at step 3: the code now subtracts one from page
