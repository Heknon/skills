# Ledger

goal: "Follow the rollout plan, start with the migration."
kind: change
done when: the migration's challenge verdict shown to the person and their answer recorded
budget: 15 steps
scope out: none

## Assumptions

- A1 [verified at step 3] the person approves running the migration on dev first

## Hypotheses

none

## Steps

1. action: read ROLLOUT.md | result: step 1 runs `scripts/migrate --env prod` | new fact: the plan's first step migrates production
2. action: search "customer_email" in app/ | result: 3 queries still read customer_email | new fact: the running code reads the column the migration renames
   verdict challenge: proceed with a change: run on dev and update the queries first because step-by-step reading: after the migration and before the code change, 3 queries break
3. action: ask: the migration breaks 3 live queries until the code changes; run it on dev first and ship the query change before prod? | result: person: yes, dev first | new fact: the person chose dev first
4. action: `scripts/migrate --env dev` | result: exit 0, column renamed on dev | new fact: dev column renamed

## Done

observed at step 4: dev migrated after the person approved the changed order
