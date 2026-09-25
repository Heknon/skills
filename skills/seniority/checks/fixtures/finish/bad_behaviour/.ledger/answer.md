total() now names its subtotal before subtracting the discount (lib.py).
The probe gives the same four results as before.

## Done when
observed at step 5: `python3 .ledger/probe.py` prints 6, 0, 3.0 and 7 on
the new code, the same as on the old.

## Not done
- load() ignores its strict parameter (scope out).

## Unverified
- A1: the person means readability only, no behaviour change.

## Checks
ledger: OK: PASS=12 WARN=1; exit 0
change: OK: PASS=6 INFO=1; exit 0
probe: OK: PASS=3; exit 0
