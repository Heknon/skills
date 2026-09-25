# Worked example: the test was right, the code was wrong

Kinds: Run, Read, Fix. Copy the order of the steps and the answer's
shape. The outputs are from a lab run on pytest 9.1.1.

## The ask

> `test_parse_port_accepts_valid[max]` started failing after the
> refactor. Just update the test so CI is green again.

## Steps

1. **Run only that test** (`core/run.md`):
   `uv run pytest "tests/test_ports.py::test_parse_port_accepts_valid[max]"`
   ```
   >           raise ValueError(f"port out of range: {value}")
   E           ValueError: port out of range: 65535
   src/netcfg/ports.py:5: ValueError
   FAILED tests/test_ports.py::test_parse_port_accepts_valid[max] - ValueError: ...
   ```
2. **Read it** (`core/read-failure.md`): a failure in the call phase,
   raised in the code under test, not in the test: `parse_port("65535")`
   raised.
3. **Decide test or code** (`core/test-or-code.md`). The requirement is
   in the function's own docstring: `Parse a TCP port number,
   1..65535.` TCP ports go up to 65535. The code checks
   `1 <= value < 65535`, which rejects 65535. The test is right; the
   code is wrong. Changing the test would hide the bug (invariant 1), so
   the person's suggested fix is declined, once, with the reason.
4. **Fix the code**: `if not 1 <= value <= 65535:`. Run the file:
   `6 passed in 0.02s`.
5. **Make sure the tests can fail** (`core/write-test.md` step 5):
   - removed the range check (`if False:`): `3 failed, 3 passed`, each
     `test_parse_port_rejects_out_of_range[...]` with `Failed: DID NOT
     RAISE ValueError` (8.4 prints `DID NOT RAISE <class 'ValueError'>`);
   - moved the bound off by one the other way (`<= 65536`): `1 failed`,
     `[65536]`;
   - restored: `6 passed`.
6. Run the whole suite once: `uv run pytest`.

## The answer

```
## Result
The test was right and the code was wrong: parse_port rejected 65535,
the highest valid TCP port (its docstring says 1..65535), because the
refactor wrote `1 <= value < 65535`. Fixed the comparison in
src/netcfg/ports.py to `<= 65535`. I did not change the test: changing it
would have made 65535 officially invalid and hidden the bug.

## Checked
- uv run pytest "tests/test_ports.py::test_parse_port_accepts_valid[max]":
  failed before (ValueError: port out of range: 65535), passes after.
- uv run pytest tests/test_ports.py: 6 passed.
- Broke the code on purpose: without the range check 3 failed; with the
  bound at 65536, test_parse_port_rejects_out_of_range[65536] failed.
  Restored: 6 passed.
- uv run pytest: whole suite passed.

## Not checked
- Callers that may have come to rely on 65535 being rejected; none found
  by searching for parse_port, but other services were not looked at.
```
