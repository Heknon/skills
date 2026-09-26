---
name: pydantic
description: Write, read and fix code built on pydantic v2, pydantic-settings and pydantic-partial. Models, fields, defaults, required and Optional, validators (field and model; before, after, wrap, plain), serializers, model_dump and model_validate, aliases and camelCase output, computed fields, strict and lax, Annotated constraints, unions and discriminators, generics, forward references and model_rebuild, TypeAdapter, reading a ValidationError, why pyright, basedpyright or mypy flags a model, migrating v1 code (validator, root_validator, .dict(), parse_obj, class Config). Settings from environment variables, .env files and secrets directories, prefixes, nesting, source order, extra keys, and tracing which source set a value. PATCH and PUT bodies with partial models (pydantic-partial, exclude_unset, unset against null, nested partials, validators on partials) and what they hand to the endpoint and the database. Verified on pydantic 2.13.5, pydantic-settings 2.15.0 and pydantic-partial 0.11.1, with older releases where they differ.
---

# Pydantic

This skill knows how pydantic v2, pydantic-settings and pydantic-partial
behave, and every API, option, default and message in it was run in a
lab on the versions it names. Nothing is written from memory: v1 habits
look right and are wrong. Find the fact here, or settle it with a probe
(`core/probe.md`) or a line of the installed source.

Read this file, then load only what the task needs.

## Read the versions first

```
uv pip show pydantic pydantic-settings pydantic-partial
```

It prints `Name:` and `Version:` for each, and `warning: Package(s) not
found for: ...` for one that is not installed (*lab*, uv 0.8.17).

Facts that changed inside 2.x carry the minor that brought them
(`reference/versions.md`). pydantic-partial changed its API between
releases: for any partial model, read `partial/check-installed.md`
first. Run everything through uv: `uv run --no-sync python probe.py`.

## The kinds of task

| Kind | You were asked to | Load |
| --- | --- | --- |
| **Model** | write or change a model, its fields, defaults, config | `core/model.md`, `typing/required-and-optional.md` |
| **Validate** | add or fix a validator, a constraint, a coercion rule | `core/validate.md`, `typing/annotated.md` |
| **Serialize** | change what `model_dump` or the JSON looks like: aliases, excludes, serializers, computed fields | `core/serialize.md` |
| **Read error** | explain a `ValidationError`, a "not fully defined" or schema error, a crash inside validation | `core/read-error.md` |
| **Type** | `Annotated`, unions, generics, `Optional`, forward refs, `TypeAdapter`, strict and lax | `typing/<topic>.md`: `required-and-optional`, `annotated`, `unions`, `generics`, `forward-refs`, `type-adapter`, `strict-and-lax` |
| **Checker** | say why pyright, basedpyright or mypy flags a model, and fix it | `core/checker.md`, `typing/checkers.md` |
| **Migrate** | move v1 code to v2, or read v1 code | `core/migrate.md`, `reference/v1-to-v2.md` |
| **Settings** | add or change settings, `.env` files, prefixes, secrets, layering, settings in tests | `settings/sources.md`, then the `settings/` file for the part |
| **Trace** | find where a setting's value came from | `settings/trace.md` |
| **Partial** | build or fix a PATCH or PUT body model | `partial/check-installed.md`, `partial/build.md`, `partial/handoff.md` |

Every kind starts with a probe when the answer is not certain:
`core/probe.md`.

## Where the facts are

| Folder | Holds |
| --- | --- |
| `core/` | the procedures: probe, model, validate, serialize, read-error, checker, migrate |
| `typing/` | required and optional, `Annotated`, unions, generics, forward references, `TypeAdapter`, strict and lax, what each checker says |
| `reference/` | config keys and defaults, v1 to v2 names, error types, what changed in each minor |
| `settings/` | sources and their order, environment variable names, `.env` files, secrets, layering, tracing, testing |
| `partial/` | checking the installed pydantic-partial, building partial models, unset against `None`, validators on partials, the hand-off to api and mongodb |
| `recipes/` | `settings/`: a layered settings module, `.env.example`, tests and `trace_settings.py`; `patch/`: partial model, apply-and-revalidate, tests. Both ran. |
| `examples/` | three finished tasks: a v1 validator migrated (`migrate-v1-validator.md`), a value traced (`trace-a-value.md`), a PATCH fixed (`fix-a-patch.md`) |

`glossary.md` fixes the words. Other skills own neighbouring ground:
api (what PATCH and PUT mean over HTTP, turning a `ValidationError`
into a response), mongodb (writing a patch as a dotted `$set`), linting
(running and configuring the checkers), deployment (where values are
injected), pytest (`monkeypatch`, fixtures), offline-docs (finding and
reading an installed package).

## Invariants

1. **v2 names only.** No `@validator`, `@root_validator`, `.dict()`,
   `.json()`, `.parse_obj()`, `class Config`, `orm_mode`, `__fields__`,
   `Field(regex=)` or `const=` in new code, even beside old code that
   uses them (`reference/v1-to-v2.md`).
2. **A claim about behaviour is backed by a probe you ran** or a line of
   installed source, and the answer quotes it.
3. **`Optional[X]` does not make a field optional to send.** Only a
   default does (`typing/required-and-optional.md`).
4. **A validator raises `ValueError`, `AssertionError` or
   `PydanticCustomError`.** Anything else, and any error from code that
   assumed the input's type, escapes as a crash, not a
   `ValidationError`.
5. **Never silence a checker with a bare `# type: ignore`, a `cast`, or a
   field made `Optional`.** Find the rule behind the message
   (`core/checker.md`).
6. **A secret never appears**: not printed, not logged, not in
   `model_dump()` output you paste. Show presence or length.
7. **A setting's source is traced, not guessed.** Before editing `.env`,
   find which source wins (`settings/trace.md`).
8. **A PATCH is validated twice**: the body with the partial model, the
   merged result with the full model. `model_copy(update=...)` validates
   nothing (`partial/handoff.md`).
9. **Unset is not `None`.** A patch is dumped with `exclude_unset=True`,
   never with `exclude_none` or `exclude_defaults`, which stop a client
   from clearing a field (`partial/unset-and-none.md`).
10. **No new packages.** Air gapped: use what is installed, and say what
    is missing.

## What you say when you finish

End with these headings, each with `none` when empty. If another skill
is loaded, its headings come first and these after.

```
## Result
<what changed, or the answer, with paths; for a trace, the winning source>

## Checked
<each probe or test run and the lines of output that show the verdict,
with the installed versions>

## Not checked
<versions, platforms (Windows, PowerShell 5.1) or paths not tried>
```

The `evals/` folder is for people testing this skill. Never open it while
doing a task.
