# Where new code goes

**Verdict you produce:** the list of files added or changed, each placed
by a line of the structure card, and the tests run.

```
file:     <path> (new | changed)
because:  <card line: layout, precedent path:line, or layer rule>
test:     <test file and what it pins>
run:      <summary line>
```

## Steps

1. **Have the card** (`core/recognise.md`). The feature you touch and its
   nearest sibling are the templates.
2. **Split the change into jobs**: a route, a request or response model,
   a rule, a query, a mapping, a provider, an error, a constant. Place
   each job with `core/layers.md`, in the file the card names for that
   job in this feature.
3. **One new thing at a time** (an exception, a constant, a helper):
   `placement/place-a-thing.md`.
4. **New files only when the feature's siblings have that file.** A
   feature with `router.py`, `crud.py`, `schemas.py` gets no
   `service.py` for one route. A new feature copies the file set of the
   most recent feature, not a textbook's.
5. **Tests where the siblings' tests are**, in their style: a route test
   through `TestClient` with an override, a service test with a fake,
   a repository test with a database if the codebase has them
   (`core/wiring.md`, "Which layer a test fakes").
6. **Run the tests**, then the whole suite. Quote the summary lines.

## Placing the usual jobs

| Job | Goes to (by feature) | Goes to (crud per feature) | Goes to (by layer) |
| --- | --- | --- | --- |
| a route | `<feature>/router.py` | `<feature>/router.py` | `routers/<feature>.py` |
| request and response models | `<feature>/schemas.py` | `<feature>/schemas.py` | `schemas/<feature>.py` |
| a rule | `<feature>/service.py` | the crud module or the route, as the siblings do; say it is a smell only if a second caller exists | `services/<feature>.py` |
| a query | `<feature>/repository.py` | `<feature>/crud.py` | `repositories/<feature>.py` |
| a provider | `<feature>/dependencies.py` | where `get_db` lives | `dependencies.py` |
| an error | `placement/custom-errors.md` | same | same |

## Never

- Never add a layer the card does not have to make room for one route
  (*eval* `crud-by-feature`: the archive endpoint is a crud function, a
  route and a schema field; `services/` is the bait).
- Never put a feature's code into another feature's module to save a
  file.
- Never change a sibling to match what you added; the change is yours
  only.
