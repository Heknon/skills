# Ledger

goal: "why is the dashboard empty?"
done when: the cause named, with the query and the log line that show it
budget: 25 steps
scope out: none

## Assumptions

none

## Hypotheses

none

## Steps

1. action: read dashboards/main.json | result: one panel, query `rate(http_requests_total[5m])` | new fact: the panel queries http_requests_total
2. action: read dashboards/main.json lines 1-40 | result: same panel | new fact: none
3. action: read README.md | result: nothing about metrics | new fact: none
4. action: read dashboards/README.md | result: nothing about metrics | new fact: none

## Done

not yet
