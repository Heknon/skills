# Defaults, when the codebase has no precedent

Use a row only after `place-a-thing.md` step 2 found no sibling of the
kind at this level. Say in the answer that a convention was started.

| Kind | Default home | Moves when |
| --- | --- | --- |
| exception | the feature's `errors.py`; base and categories in the package's `errors.py` (`app/errors.py`, or `core/errors.py` if the package has a `core/`) | never next to its first raiser |
| constant | module level, `UPPER_CASE`, in the one module that uses it | a second module needs it: the feature's `constants.py`; it differs by environment: it is a setting (pydantic-settings, the pydantic skill) |
| enum | the feature's domain or schemas module; `StrEnum` when it crosses the wire | two features share it: the shared package |
| type alias, `Protocol` | beside the code that depends on it (a repository `Protocol` beside its service) | two consumers: the shared package |
| helper | private (`_name`) in the module that uses it | a caller in another module: a module named for what it does (`money.py`, `slugs.py`) |
| provider for `Depends` | the feature's `dependencies.py` | shared by features: the package's `dependencies.py` or `db.py` |
| settings field | the one settings class | never a second settings class for one field |
| schema | the feature's `schemas.py` | never in `models.py` beside database models |

File names, with no precedent (decision AR10): `errors.py`, not
`exceptions.py`; one per feature, with the base and the categories in
the package's shared `errors.py`.

For a small app with no features yet (one `main.py`), the package's
`errors.py` holds the base, the categories and the few specific errors
until a feature folder appears (*eval* no-precedent: `app/errors.py`
with `AppError`, `ConflictError` and `DuplicateTitleError`).
