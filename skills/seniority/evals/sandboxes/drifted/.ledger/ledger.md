# Ledger

goal: "what is the default cache TTL, and which environment variable changes it?"
done when: the default and the variable named, each with the file and line that sets it
budget: 8 steps
scope out: none

## Assumptions

- A1 [unverified] the TTL is set in a config file

## Hypotheses

none

## Steps

1. action: search "ttl" in config/ | result: no such directory | new fact: there is no config/ directory
2. action: search "ttl" in config/ | result: no such directory | new fact: none
3. action: read app/README.md | result: configuration is read from environment variables in app/settings.py | new fact: none
4. action: search "ttl" in *.yaml | result: no files | new fact: none

## Done

not yet
