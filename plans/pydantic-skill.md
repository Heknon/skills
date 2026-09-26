# Plan: the pydantic skill

Status: built in `skills/pydantic/`. The defaults in section 10 were
taken so the skill could be built; each can be changed. Sections 11 and
12 say how it was verified and what the lab changed.

## 1. What it is

The knowledge needed to write, read and fix code built on pydantic v2:

1. **Models**: fields, defaults, validators (field and model; before,
   after, wrap, plain), serializers, `model_dump`, `model_validate`,
   `TypeAdapter`, aliases, strict and lax, computed fields, config; the
   typing under them (`Annotated` and constraints, generics,
   discriminated unions, `Optional[X]` against a default against
   required-nullable, forward refs and `model_rebuild`, how mypy and
   pyright see a model); and the v1 to v2 traps.
2. **Settings** (`settings/`): pydantic-settings, `.env`, prefixes and
   nesting, secrets directories, source order, layering, and tracing
   where a value really came from.
3. **Partial models** (`partial/`): PATCH and PUT bodies built with
   `pydantic-partial`, nested partials, unset against `None`, validators
   on partials, and the hand-off to api and mongodb.

api and mongodb stand on it, so it is built first. Its core rule: a
claim about pydantic is backed by a probe run here or a line of installed
source, never by memory, because v1 habits look right and are wrong.

## 2. The environment it is written for

- **A weak model** (MiniMax 2.7 for evals) in Zed's agent on Windows with
  PowerShell, air gapped, no web; Python through uv, packages only from
  the internal mirror. A missing package is reported, not worked around.
- **Whatever version is installed.** The model reads it first
  (`uv pip show pydantic pydantic-settings pydantic-partial`). Facts that
  changed inside 2.x carry the minor that brought them.
- **pydantic-partial has changed names.** Up to 0.3.x it had only
  `as_partial`; `model_as_partial` exists from 0.5.0 and `as_partial` now
  warns; `partial_cls_name` came in 0.7.0; 0.9.0 dropped pydantic v1. So
  `partial/` opens by reading the installed `pydantic_partial/partial.py`
  (under 200 lines) before any code is written. How to find it is
  offline-docs' ground.
- **Probes, not memory.** A question is settled by a short script run
  with `uv run --no-sync python probe.py`, written to a file because
  PowerShell 5.1 mangles quotes passed to `python -c` (to verify in the
  lab on 5.1 and 7).
- **Windows and settings.** Variable names are case-insensitive on
  Windows; `$env:APP_PORT = "1"` lives only in that session; PowerShell
  5.1 `>` writes UTF-16, and a UTF-16 `.env` fails to load (a
  `UnicodeDecodeError` on Linux; on Windows, to verify in the lab).

## 3. The kinds of task

| Kind | Asked to | Answer shape |
| --- | --- | --- |
| **Model** | write or change a model, its fields, defaults, config | the model, and a probe that shows valid and invalid input |
| **Validate** | add or fix a validator, a constraint, a coercion rule | the validator with its mode named, and the probe's accepted and rejected inputs |
| **Serialize** | change what `model_dump` or JSON output looks like: aliases, excludes, serializers, computed fields | the dumped output before and after |
| **Read error** | explain a `ValidationError` or a schema-build error | each `loc`, `type` and `input`, and the line that raised it |
| **Type** | a typing question: `Annotated`, unions, generics, `Optional`, forward refs, `TypeAdapter` | the rule, and a probe that shows it |
| **Checker** | say why mypy or pyright flags a model, and fix it | the message, the rule behind it, the fix; no bare `type: ignore` |
| **Migrate** | move v1 code to v2, or read v1 code | each change with its v1 and v2 names, and the tests run |
| **Settings** | add or change settings, `.env` files, prefixes, secrets, layering | the settings class, the variable name each field reads, a probe |
| **Trace** | find where a setting's value came from | the winning source and every source that also set it, secrets masked |
| **Partial** | build or fix a PATCH or PUT body model | the installed pydantic-partial version, the partial model, what it hands to the endpoint |

## 4. The failures it targets

| Failure | What it looks like |
| --- | --- |
| **v1 from memory** | `@validator`, `@root_validator`, `.dict()`, `.parse_obj()`, `class Config`, `orm_mode`, `__fields__`, `Field(regex=)`, `const=` written into v2 code |
| **Optional means optional** | `x: Optional[int]` with no default, then surprise that `x` is required; or `= None` added where the field must be sent, even as `null` |
| **Wrong validator mode** | a `before` validator calls `.strip()` on raw input that may be an int; a `wrap` validator never calls the handler; `TypeError` raised, which escapes as a crash, not a `ValidationError` (seen on 2.13.5) |
| **v1 coercion assumed** | expects `int` to reach a `str` field, or a union to try members left to right; v2 is stricter and unions are "smart" |
| **Union without a tag** | fields made `Optional` until every payload fits every member, instead of a `Literal` discriminator |
| **Forward ref fought** | "not fully defined" answered with `Any` or by moving classes, instead of `model_rebuild()` after both exist |
| **Alias confusion** | fields renamed because output is snake_case, when `by_alias=True` or `serialize_by_alias` was the fix; construction by field name fails and `populate_by_name` is set blindly |
| **Checker silenced** | `# type: ignore` or `cast` on a model error, or a field made `Optional` to please the checker |
| **`.env` not read** | `env_file=".env"` is relative to the working directory, so run from elsewhere the defaults load with no error (seen on 2.15.0); the model hard-codes the value |
| **Wrong source blamed** | edits `.env` again and again while a shell variable or a secrets file wins over it |
| **Extra keys** | a key in `.env` that no field matches fails with `extra_forbidden`, even without the prefix (seen on 2.15.0); the model deletes other tools' keys or sets `extra="allow"` |
| **Secret shown** | prints settings, or `model_dump()` of them, into a log or the answer |
| **Settings frozen at import** | a module-level `settings = Settings()` that tests cannot change; blamed on pytest |
| **Partial API guessed** | `Model.partial()`, `as_partial` on a new version, `partial_cls_name` on 0.5.x |
| **Unset written as null** | `model_dump()` without `exclude_unset=True`: PATCH nulls fields it never sent and resets defaulted ones; or `exclude_none=True`, so a client cannot clear a field |
| **Nested partial assumed** | `recursive=True` expected to reach a nested model that does not use `PartialModelMixin`; it stays full (seen on 0.11.1) |
| **Validators on partials** | the base model's validators are inherited; with `None` they crash with `AttributeError` (a 500), or are deleted to make PATCH work |
| **Constraints lost** | on a required field the partial copy drops `min_length`, `max_length` and similar, so PATCH accepts what create rejects (seen on 0.11.1 with 2.13.5; to reconfirm) |

## 5. Layout

```
skills/pydantic/
  SKILL.md, glossary.md  router over the ten kinds, invariants, headings
  core/        probe (settle a question with a script), model, validate,
               serialize, read-error, checker, migrate (v1 to v2)
  typing/      required-and-optional, annotated, unions, generics,
               forward-refs, type-adapter, strict-and-lax, checkers
  reference/   config keys and defaults, v1 to v2 names, error types
               seen, what changed in each 2.x minor
  settings/    sources (order, merge, customising), env (prefix, alias,
               case, nesting, PowerShell), dotenv (path, encoding, extra
               keys), secrets, layering, trace, testing
  partial/     check-installed, build (fields, dotted, recursive),
               unset-and-none, validators, handoff (to api and mongodb)
  recipes/     settings/ (layered module, `.env.example`, trace script);
               patch/ (partial model, apply-and-revalidate, tests)
  examples/    a v1 validator migrated, a value traced, a PATCH fixed
  evals/       evals.json and sandboxes
```

## 6. Dependencies and boundaries

| Skill | Needs | Relies on by name | Existing skills it touches |
| --- | --- | --- | --- |
| pydantic | none | offline-docs | deployment (where config values come from) |

- **Needs none**: it is the base of wave 1.
- **offline-docs**: how to find and read an installed package; pydantic
  says which file and names to look for (`partial/check-installed.md`).
- **deployment** owns where values are injected (CI variables,
  ConfigMaps, Secrets); `settings/layering.md` starts where the variable
  reaches the process.

| Ground | Owner | The other side |
| --- | --- | --- |
| partial models (`pydantic-partial`, `exclude_unset`, unset vs `None`) | pydantic | api owns PUT vs PATCH semantics; mongodb owns turning a patch into a dotted `$set` |
| settings and config management | pydantic | deployment owns where values are injected |
| what pydantic types mean | pydantic | linting owns running the checkers, their config and the mypy plugin setting |

The hand-off is one object: the nested dict from
`model_dump(exclude_unset=True)`. api decides whether it may be a patch
or, for PUT, must be a full model; mongodb flattens it into dotted paths.
For R2, the pydantic pin must satisfy the FastAPI and Beanie pins, and
the mypy and pyright pins must match linting's.

### Proposed changes to the roadmap

1. **Add documentation to "touches".** Its `python/surfaces.md` greps
   `BaseSettings`, but a field's variable name depends on prefix, alias,
   nesting delimiter and case; pydantic should own that rule.
2. **Add pytest to "touches".** Settings in tests (`_env_file=None`, a
   developer's `.env` leaking in, cached getters) meet `monkeypatch`,
   which pytest owns.
3. **Add linting, api and mongodb to "relies on by name"**: the Checker
   kind hands running a checker to linting, and `partial/handoff.md`
   points at api and mongodb, which are built later, so those pointers
   must read sensibly while they are absent.
4. **A tension with mongodb.** If PD4 is taken, an update becomes read,
   merge, validate, write, which a single dotted `$set` avoids. mongodb
   owns the write, pydantic what must be validated; both plans should say
   so.

## 7. How it will be verified

Pins (public index, 2026-09-25; the mirror may differ, PD1): Python 3.12,
pydantic 2.13.5 (pydantic-core 2.46.5), pydantic-settings 2.15.0,
pydantic-partial 0.11.1 plus one older release (PD3), mypy and pyright
at linting's pins (the index has mypy 2.3.1, pyright 1.1.414).

The lab must: run every fact as a probe kept beside the file that states
it, or mark the fact *not run*; record mypy (with and without
`pydantic.mypy`) and pyright output verbatim for each model shape; run
the settings recipe from two working directories with each source on and
off and record which wins; run the partial recipe on each pinned
pydantic-partial and diff the releases' `partial.py` for the API table;
run the Windows facts on PowerShell 5.1 and 7, or mark them *not run*.

A first probe for this plan (Linux, Python 3.11, the pins above) showed:
the default order is init arguments, environment, `.env`, secrets
directory, defaults; nested values merge across sources; a trailing
newline in a secrets file is stripped; the partial class is a cached
subclass of the base and keeps defaulted fields as they were; and the
findings marked "seen" in section 4. All to reconfirm on Python 3.12.

## 8. Evals, written first

Sandboxes, uv projects on the pinned versions, each baiting one failure:

| Sandbox | Bait |
| --- | --- |
| `optional-required` | "clients may omit `nickname`"; the field is `Optional[str]` with no default |
| `v1-validator` | "add a check that `sku` is upper case" in a v2 codebase with one old `@validator` to copy |
| `before-mode` | a `before` validator crashes on an int; the obvious fix is `str(v)` everywhere |
| `pet-union` | `Cat` payloads parse as `Dog`; the easy fix is more `Optional` fields |
| `two-modules` | `Order` and `Customer` refer to each other across files: "not fully defined" |
| `camel-output` | the API must return camelCase; aliases exist but the dump omits `by_alias` |
| `pyright-alias` | Zed flags a model with aliases (the message is to record in the lab); bait is `# type: ignore` |
| `env-cwd` | the service ignores `.env` when started from the repository root |
| `who-set-port` | port is 9000; `.env` says 7000; a secrets file and a stale variable exist |
| `shared-dotenv` | `.env` also holds another tool's keys: `extra_forbidden` on start |
| `patch-resets` | PATCH `{"name": "x"}` nulls `email` and resets `status` to its default |
| `nested-partial` | `recursive=True` but the nested `Address` still needs every field |
| `partial-500` | PATCH with `"name": null` gives a 500 from an inherited validator |
| `partial-old` | pydantic-partial 0.5.5 installed (to verify it runs on 2.13.5); the task needs a named partial class |
| `patch-min-length` | PATCH accepts a two-letter name that create rejects |

Each eval names what a good answer quotes (probe output, installed
version, winning source) and must not do (delete a validator, print a
secret). Every bait and fix is reproduced on the pins first.

## 9. Decisions needed

### PD1. Versions

Which releases do the mirror and the services have? *Recommended:*
2.13.5 and the oldest 2.x minor in use; `reference/versions.md` covers
what lies between.

### PD2. How much v1

*Recommended:* migration and reading only; `pydantic.v1` imports are a
step in a migration, never new code.

### PD3. Which pydantic-partial releases

*Recommended:* 0.11.1 plus the release the services have. The API table
starts at 0.5: 0.3.x needs pydantic v1, and 0.5.0 caps pydantic below
2.1, so the first 0.5 release usable on current 2.x is to verify.

### PD4. The answer to lost constraints and crashing validators

Options: validate the merged result with the full model before writing;
write patch models by hand; make every base validator `None`-safe.
*Recommended:* apply the patch to the stored object and validate the
result with the full model, if the lab confirms the loss. It also catches
rules across fields. See section 6, proposed change 4. Reconciled with
mongodb's dotted `$set` in `plans/roadmap.md`, decision R4.

### PD5. Settings sources

pydantic-settings 2.15 also reads TOML, YAML, JSON, `pyproject.toml`, the
command line and cloud secret stores. *Recommended:* environment, `.env`
and secrets directory in depth; one file source only if the team layers
with files; no cloud stores (air gapped).

### PD6. A trace script

*Recommended:* ship `recipes/settings/trace_settings.py`: it builds each
source alone and prints, per field, every source that set it, secrets
masked. `settings/trace.md` also teaches the steps by hand.

### PD7. Which checker the skill explains first

A model in Zed sees its language server's errors about models before it
runs anything. *Recommended:* explain that server first (pyright or
basedpyright, to verify), then mypy with the plugin. linting owns their
configuration.

## 10. Decisions taken as defaults

- **PD1. Versions.** pydantic 2.13.5 (pydantic-core 2.46.5),
  pydantic-settings 2.15.0, pydantic-partial 0.11.1, Python 3.12, all
  available on the public index. Where behaviour differs, 2.10.6,
  2.11.10 and 2.12.5 were run too (`reference/versions.md`); the
  mirror's versions are still to confirm.
- **PD2. v1 for migration and reading only.** `core/migrate.md` uses the
  bundled `pydantic.v1` (1.10.26) to show what v1 code did; it is never
  the target for new code.
- **PD3. pydantic-partial releases.** 0.11.1, plus every release that
  installs on pydantic 2.13.5 (0.5.2 to 0.10.2), diffed and probed;
  0.5.5 backs the `partial-old` eval.
- **PD4. Validate the merged result with the full model** (roadmap R4).
  The lab confirmed the losses, and added two rules the merge needs:
  field validators return `None` unchanged, and model validators return
  early when the partial is parsed with `context={"partial": True}`
  (`partial/validators.md`, `recipes/patch/`).
- **PD5. Environment, `.env` and secrets in depth**; adding a TOML
  source is shown in `settings/sources.md`; other file sources, the
  command line and cloud stores are named only.
- **PD6. The trace script** ships as `recipes/settings/trace_settings.py`
  and ran; `settings/trace.md` also gives the steps by hand.
- **PD7. basedpyright first.** Zed's documentation says basedpyright is
  its default Python server since 0.204.0, in `standard` mode; the lab
  ran basedpyright 1.40.1, pyright 1.1.414 and mypy 2.3.1 with and
  without the plugin (`typing/checkers.md`).

## 11. How it was verified

Every API, option, default, message and behaviour in the skill was run
in a lab outside the repository on Linux, Python 3.12.3, uv 0.8.17, with
the pins above, or read in the installed source (marked *source*).
Probes stayed in the lab, outside the repository. In detail:

- The fifteen evals were written first; each bait was reproduced in a
  fresh copy of its sandbox and each intended fix passed its tests.
- Settings: the source order on pydantic-settings 2.8.1, 2.12.0 and
  2.15.0; each `.env`, secrets and variable-name fact on 2.15.0; the
  settings recipe's six tests on 2.15.0 and 2.14.1 (and the expected
  failure on 2.13.1); the trace script on 2.15.0 and 2.12.0, run from
  several working directories with each source on and off.
- Partial models: `partial.py` and `utils.py` diffed across 0.3.4 to
  0.11.1; the three problems probed on every installable release; the
  patch recipe's eleven tests on pydantic-partial 0.9.0, 0.10.2 and
  0.11.1, on pydantic 2.12.5 and 2.13.5 (and, with two arguments
  removed, 2.11.10 and 2.10.6), and shown to fail against the naive
  versions.
- Checkers: pyright 1.1.414, basedpyright 1.40.1, mypy 2.3.1 with and
  without `pydantic.mypy`, output recorded for each model shape.
- The three examples are lab runs with their real output.
- Not run: anything on Windows or PowerShell (marked *not run on
  Windows*: `$env:` scope, `setx`, case-insensitive variable names,
  PowerShell 5.1 writing UTF-16 with `>`, quoting in `python -c`), and
  Zed itself (its default server is from its documentation).

## 12. What the lab changed

Findings that corrected the plan or a common belief, each now in the
skill:

- `recursive=True` also skips nested models on fields **with a
  default** (`work: Addr | None = None`), even with the mixin: only
  required fields are rebuilt. Listing the field as `"work.*"` works.
- Inherited **model** validators run on the partial instance, which
  holds defaults, not stored values: a valid PATCH was rejected
  (`min_items` 15 against the partial's default `max_items` 10, stored
  20), and with required fields they crash on `None`. A validation
  context flag fixes it.
- Validating the merged result re-runs validators on stored values: a
  hashing validator re-hashed a stored hash. Validators must be
  idempotent.
- The hand-off must carry values from the validated model, not the raw
  body: a tidying validator rewrote `"  Bea   Stone "`.
- Constraints are lost on required fields only, and all of them (`gt`,
  `pattern`, `StringConstraints`), not only lengths; releases before
  0.10.2 also print a `metadata` deprecation warning.
- pydantic-partial history: 0.8.0, not 0.9.0, dropped pydantic v1;
  0.5.2 is the first release installable on current 2.x; 0.7.0 and
  0.8.0 crash with `TypeError: type 'types.UnionType' is not
  subscriptable` on `X | None` fields with `recursive=True`. The
  partial class is typed as the full model, so construct it with
  `model_validate`; mypy rejects subclassing it, so name it with
  `create_model`.
- Unknown config keys are ignored silently: `serialize_by_alias` on
  pydantic 2.10, `dotenv_filtering` on pydantic-settings 2.13. v1's
  `allow_mutation=False` leaves a v2 model mutable with only a warning.
- For a shared `.env`, `dotenv_filtering="match_prefix"` (2.14+) is
  better than the plan's `extra="ignore"`: other tools' keys are
  ignored and misspelt `APP_` keys still fail.
- The plain secrets source does not split nested names
  (`app_db__password` sets nothing); `NestedSecretsSettingsSource`
  (2.12+) does. A settings field with `validation_alias` ignores
  `env_prefix`. `PYDANTIC_SETTINGS_DEBUG` (2.15) logs secrets in clear.
- Checkers: `Field(validation_alias=, serialization_alias=)` keeps
  pyright, basedpyright and mypy quiet where `Field(alias=)` fights one
  or the other; basedpyright's `recommended` mode flags an unannotated
  `model_config` (`ClassVar[ConfigDict]` fixes it).
- Probes: a probe named `types.py` or `pydantic.py` shadows the module;
  a `src/` project without a build system needs `PYTHONPATH=src` for a
  probe; `StringConstraints` checks `pattern` before `to_upper`.

The plan's section 7 claims were all reconfirmed on Python 3.12: the
default order, nested merging, the stripped newline in secrets, the
cached subclass, the relative `.env` path, `extra_forbidden` without the
prefix, the `TypeError` escaping from a validator, and the three
partial-model problems.
