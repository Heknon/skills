# Replace a magic value

Give a literal (`0.2`, `30`, `"EUR"`) a name as a module constant.

## Preconditions

- Each occurrence to replace means the same thing. `0.2` as the VAT
  rate and `0.2` as the VIP discount are two constants, not one.
- The constant is not a setting that differs per environment: that is
  a setting (the pydantic skill's), not a constant.

## Mechanics

1. Add the constant at the top of the module, with a comment when the
   name does not say the unit: `GRACE_DAYS = 30`.
2. Replace the occurrences that mean it, one meaning per step.
3. Checks; commit: "Name the VAT rate".

## Traps seen in the lab

| Trap | What happened |
| --- | --- |
| the constant used as a default: `def with_vat(net, rate=VAT)` | the default is fixed when the `def` runs. After `VAT` was changed to 0.1, `with_vat(100)` still gave `120.0`; a default of `None` read at call time gave `110.00000000000001`. If code or tests change the constant at run time, the two forms differ |
| another module imports the constant by name (`from pricing import VAT`) | it holds its own copy; patching `pricing.VAT` does not reach it (pytest's `core/mocking.md`: patch where used) |

Seniority's change check reports a changed module constant as a
warning (`module-constants`) and a removed public one as a failure
(`public-signature`, `was removed or renamed`); a new one is not
reported.

## Probe inputs

The functions that use the value, with and without their defaults.

**Done when:** every occurrence that means the constant uses it, the
others are untouched, and the checks and probe are unchanged.
