Review of "Add transfer of loyalty points between accounts" (feature, first commit)

## Verdict
changes needed: one major finding.

## Findings
[1 major] src/shop/points.py:29
  when: transfer_points(ann, bob, -20) -> ann gains 20 points and bob
        loses 20: a negative amount reverses the transfer, so anyone can
        take points from another account
  evidence: read src/shop/points.py:29-32
  suggest: refuse points <= 0 before the balance check

[2 minor] src/shop/points.py:35
  when: audit() raises (the audit store is down) -> the transfer happens
        and nothing records it; nobody is told
  evidence: read src/shop/points.py:33-36
  suggest: let it raise, or log the exception before carrying on

[3 minor] tests/test_points.py
  when: the balance check at src/shop/points.py:29 is changed or removed
        -> no test fails
  evidence: ran uv run --no-sync pytest -q: 2 passed; no test raises
        InsufficientPoints
  suggest: a test that transfers more than the balance

## Checked
- uv run --no-sync ruff check .: All checks passed!
- uv run --no-sync mypy: Success: no issues found in 3 source files
- uv run --no-sync pytest -q: 2 passed

## Not reviewed
none
