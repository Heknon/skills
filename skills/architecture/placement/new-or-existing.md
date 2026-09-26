# A new file, or an existing one

**Verdict you produce:** join `<path>` or create `<path>`, with the rule.

## Join an existing file when

- a file already holds this kind at this level: the feature's
  `errors.py` for a feature error, the package's `errors.py` for a new
  category, the module that holds the feature's other constants;
- or the codebase keeps everything of this kind in one central file
  (one `app/errors.py`, one `app/constants.py`), whatever its size.

## A new file earns its place only when

- the kind has no home at this level and the codebase gives kinds their
  own files elsewhere (other features have `errors.py`; this one has
  none yet): create the same file name here;
- or joining would mix two layers or two features in one file (a
  feature's error into another feature's `errors.py`; an HTTP schema
  into `models.py` of database models).

## Never

- **One file per class**: `order_not_found_error.py`.
- **A new grab bag**: `utils.py`, `helpers.py`, `common.py`, `misc.py`.
  A new module is named for what it does (`slugs.py`, `money.py`).
- **A second home for a kind that has one**: `errors.py` beside
  `exceptions.py`, `constants.py` beside `config.py`'s constants,
  `enums.py` when enums live in `schemas.py`.
- **A home chosen to dodge an import cycle.** A circular import after
  placing something means it was placed in the wrong layer (usually too
  low a module importing a higher one): move it down to where both
  importers can reach it, or move the code that needs it up. Never fix
  it with a function-level import (L7; *lab,* sandbox circular: the local
  import made the app start and hid the cycle, and ruff `PLC0415`
  flagged it).

## Size is not a reason

A long `errors.py` of one kind is fine: it is where readers look. A long
module of mixed kinds (a 900-line `utils.py`) is a grab bag: it is not a
precedent for where a new subject goes (`helpers.md`).
