# Helpers

**Verdict you produce:** where a helper function goes, with its
precedent.

## The order

1. **Private first.** A helper used by one module is `_name` in that
   module, below its caller. Most helpers stay here.
2. **A second caller in another module.** Look at what the callers
   already import: the module they both import shared helpers of this
   subject from is the precedent (`^from\s+\S+\s+import` in each
   caller). Join it.
3. **No such module.** Create one named for what it does (`slugs.py`,
   `money.py`, `dates.py`) in the lowest package both callers can
   import without a cycle. Say a convention was started.

## Grab bags

A module named for nothing (`utils.py`, `helpers.py`, `common.py`,
`misc.py`) shows that the codebase shares helpers, not where a new
subject goes. Do not append to one, and never create one.

*eval* utils-dump: `app/utils.py` is 898 lines of mixed helpers whose
docstring says `Please do not add to this file`; `app/text.py` holds
three text helpers (`normalise_whitespace`, `ascii_fold`, `word_count`)
and both `articles/service.py` and `tags/service.py` import from it.
The lab's fix put `slugify` in `app/text.py`, reusing `ascii_fold`
(`'Crème Brûlée'` became `'creme-brulee'`), and the four tests passed.
A new `app/slugs.py` would also be acceptable, with the reason; a
function appended to `utils.py`, a copy of `ascii_fold`, or a new
`helpers.py` would not.

When a grab bag is the only place helpers live, keep your helper
private if you can; if it must be shared, start a purpose-named module
beside the grab bag and say why. Moving the grab bag's contents is a
refactoring, and not part of the task.

## Never

- Never put a helper in a feature module so another feature can import
  it: features do not import each other's internals.
- Never copy a helper that exists; import it.
- Never make a helper public (drop the `_`) only to test it: test the
  function that uses it.
