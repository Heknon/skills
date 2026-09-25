# Ledger

goal: "start the dev server"
done when: `curl -s localhost:8000/health` prints ok
budget: 15 steps
scope out: none

## Assumptions

none

## Hypotheses

none

## Steps

1. action: `make dev` | result: exit 2, address already in use | new fact: port 8000 is taken
2. action: `make dev` | result: exit 2, address already in use | new fact: none
3. action: read Makefile target dev | result: runs uvicorn on port 8000 | new fact: none
   stuck: rerunning make dev -> find what holds port 8000
4. action: `make dev` | result: exit 2, address already in use | new fact: none

## Done

not yet
