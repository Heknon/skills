# Ledger

goal: "install the dependencies and run the tests"
done when: `pytest` exits 0
budget: 15 steps
scope out: none

## Assumptions

none

## Hypotheses

none

## Steps

1. action: `pip install -r requirements.txt` | result: exit 1, Could not find a version that satisfies the requirement torch==2.3.1 | new fact: torch 2.3.1 is not in the reachable index
2. action: `pip install -r requirements.txt` | result: exit 1, Could not find a version that satisfies the requirement torch==2.3.1 | new fact: none
3. action: `pip install  -r requirements.txt` | result: exit 1, Could not find a version that satisfies the requirement torch==2.3.1 | new fact: none

## Done

not yet
