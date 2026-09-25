# Ledger

goal: "where is the retry limit for the uploader set?"
done when: the setting is named with the file and line that sets it, and the file and line that reads it
budget: 8 steps
scope out: none

## Assumptions

- A1 [unverified] "the uploader" means `services/uploader`, not the CLI upload command

## Hypotheses

none

## Steps

1. action: search "retry" in services/uploader/ | result: 4 hits: config.py:12, client.py:40, client.py:55, tests/test_client.py:9 | new fact: retries are configured in config.py and used in client.py

## Done

not yet
