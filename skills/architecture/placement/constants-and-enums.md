# Constants, enums, and when a value is a setting

**Verdict you produce:** constant, enum or setting, and where it lives.

## Constant or setting

| The value | It is | Where |
| --- | --- | --- |
| fixed by the domain or the code (`MAX_NAME_LENGTH = 80`, a regex) | a constant | module level, `UPPER_CASE`, in the module that uses it (`defaults.md`) |
| the same everywhere today, but someone asks for it to differ by environment ("50 in production, 10 in the tests") | **a setting** | a field of the codebase's pydantic-settings class |
| a secret, a URL, a host, a timeout an operator tunes | a setting | same |

How settings are declared, layered, read from the environment and
overridden in tests is the pydantic skill's (`skills/pydantic/settings/`).
This file only says when a constant has become one.

*eval* constant-or-setting: `PAGE_SIZE = 20` in `app/listing.py`, and a
`Settings(BaseSettings)` class already in `app/settings.py`. The change
that passed in the lab: `page_size: int = Field(default=50, ge=1,
le=500)` in `Settings` (environment variable `CATALOGUE_PAGE_SIZE` from
the class's `env_prefix`), `listing.page(number, size)` taking the size,
the route reading `Depends(get_settings)`, and the test overriding
`get_settings` with `Settings(page_size=10)`. `MAX_NAME_LENGTH` stayed a
constant. Wrong: editing the constant, a second constant chosen by
`if os.environ.get("TESTING")`, or `monkeypatch.setattr(listing,
"PAGE_SIZE", 10)` in tests.

## Constants

- Module level, `UPPER_CASE`, typed when not obvious
  (`TIMEOUT_S: float = 5.0`), in the one module that uses them.
- A second module needs it: the feature's `constants.py` if the codebase
  has such files, otherwise the lower of the two modules (the one the
  other already imports).
- An upper-case module-level dict or list that code changes
  (`MEMBERS: dict[int, Member] = {}`) is state, not a constant: it is a
  store, and belongs behind a provider (L9).

## Enums

Use `StrEnum` (Python 3.11 and later) for a value that crosses the wire
or is stored as text. *lab,* Python 3.12.14, pydantic 2.13.5, FastAPI
0.141.1, `class Status(StrEnum): OPEN = "open"` against a plain
`Enum`:

| | `StrEnum` | plain `Enum` |
| --- | --- | --- |
| `model_dump()` | `<Status.OPEN: 'open'>` | `<Plain.OPEN: 'open'>` |
| `model_dump(mode="json")` | `'open'` | `'open'` |
| `f"{member}"` | `open` | `Plain.OPEN` |
| `member == "open"` | `True` | `False` |
| as a query parameter, `?s=nope` | 422, `Input should be 'open' or 'closed'` | same |
| OpenAPI | `{"type": "string", "enum": ["open", "closed"]}` | same |

The f-string and `==` rows are why: a plain `Enum` member in a log line
or a comparison with stored text behaves differently from its value.

Where: the feature's domain or schemas module, beside the model that
uses it; the shared package when two features use it. Not a separate
`enums.py` unless the codebase has one.

## Never

- Never make a constant a setting "in case": settings are read at start
  and documented for operators; add one when a value must differ.
- Never keep a per-environment value in code behind an environment
  check.
