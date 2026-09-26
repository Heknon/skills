# Change a signature

Add, remove, rename or reorder parameters, or change a default.

A signature is public surface. Adding a parameter with a default at the
end, or as keyword-only, keeps every existing call working. Everything
else (rename, remove, reorder, a new required parameter, a changed
default) changes behaviour for some caller: it is a refactoring step
only when every caller is in this repository and changes in the same
step, and never for a public function others may call
(`core/public-surface.md`).

## Preconditions

- Every call site is listed (`core/every-reference.md`), including
  calls with keyword arguments (`\bname\s*=` inside calls), `partial(`,
  callbacks passed by name, and overrides in subclasses (`def name\b`).
- The function is not an entry point, a hook, a framework callback or
  a registered handler whose caller passes fixed arguments.

## Mechanics: adding a parameter

1. Add it with a default that gives today's behaviour, at the end or
   after `*`:

   ```python
   def find(user_id: int, *, strict: bool = False) -> int:
   ```

2. Checks. Nothing else changes in this step.
3. Callers that need the new value are changed in later steps.

## Mechanics: any other change (parallel change)

1. Add a new function with the new signature beside the old one, or a
   new parameter beside the old.
2. Make the old one call the new one, so there is one body.
3. Move callers to the new one, a group per step.
4. Remove the old form only when asked and nothing outside calls it.

## Traps seen in the lab (Python 3.12.14)

| Change | A caller that was not changed |
| --- | --- |
| a parameter renamed | `TypeError: find() got an unexpected keyword argument 'exact'`; mypy `call-arg`: `Unexpected keyword argument "exact" for "find"`; pyright `reportCallIssue`: `No parameter named "exact"` |
| a required parameter added | `TypeError: f() missing 1 required positional argument: 'b'` |
| a parameter made keyword-only | `TypeError: g() takes 0 positional arguments but 1 was given` |
| a default changed | nothing fails; the result differs. Only the probe and seniority's change check see it |

mypy reports none of these inside functions without annotations unless
`check_untyped_defs` is set (`core/checks.md`). A default is evaluated
once, when the `def` runs: `def with_vat(net, rate=VAT)` kept 0.2 after
the module's `VAT` was set to 0.1, while a default of `None` read at
call time gave the new value (`replace-magic-value.md`).

## Probe inputs

Each call form the search found: positional, by keyword, with and
without the defaulted parameter.

**Done when:** every caller found passes the checks, the probe is
identical, and `tools/public_names.py` shows the signature line changed
only as intended.
