# Place one new thing

**Verdict you produce:** the path, the precedent, and the rule used.

```
kind:       <exception | constant | enum | type alias or Protocol | helper | settings field | schema | provider>
path:       <file, new or existing>
precedent:  <path:line of the nearest sibling of the same kind, or "no precedent: default used, convention started">
rule:       <precedent | defaults.md row | new-or-existing.md rule>
note:       <when the precedent is worse than the default, one sentence; otherwise none>
```

Layers decide the folder; placement decides the file. The rule is the
same as for layers: the codebase's precedent first, defaults only where
there is none.

## Steps

1. **Name the kind.** One of: exception, constant, enum, type alias or
   `Protocol`, helper function, settings field, schema, dependency
   provider. A value that differs between environments is a settings
   field, not a constant (`constants-and-enums.md`).
2. **Find the precedent.** Search for siblings of that kind (editor's
   `grep`, `**/*.py`, excluding `.venv`), and note which files hold them
   and how those files are named:

   ```
   exception   ^\s*class\s+\w+\(\s*[\w.]*(Error|Exception|Warning)\b[^)]*\)\s*:
   constant    ^[A-Z][A-Z0-9_]*\s*(:[^=]+)?=[^=]
   enum        ^\s*class\s+\w+\(\s*[\w.]*(StrEnum|IntEnum|Enum|Flag)\b
   Protocol    ^\s*class\s+\w+\(\s*[\w.]*Protocol\b
   type alias  ^type\s+\w+\s*=|^\w+\s*:\s*TypeAlias\s*=
   settings    ^\s*class\s+\w+\(\s*[\w.]*BaseSettings\b
   provider    Depends\(\s*\w+        then locate each name it lists
   grab bags   files named utils*, helpers*, common*, misc*, shared*
   ```

   For a helper, read the imports of the modules that will call it
   (`^from\s+\S+\s+import` in each caller): the module they already
   import shared helpers of that subject from is the precedent
   (`helpers.md`).
3. **Precedent wins over the defaults**, even when the default is
   better: `exceptions.py` stays `exceptions.py`, one central errors file
   stays central. Say so in `note` when it matters; do not migrate
   unasked.
4. **Same level.** A precedent counts at the level of the new thing: a
   feature error follows where that feature, or its siblings, keep
   feature errors; a shared category follows where the base lives.
5. **Existing file or new**: `new-or-existing.md`.
6. **No precedent**: use `defaults.md`, and say that a convention was
   started and what it is.
7. **Answer** with the verdict block. Give the precedent as `path:line`
   you read, not the search hit alone.

## What the searches miss (*lab*, ripgrep's regex, the same syntax as the editor's `grep`)

| Missed or misleading | Seen as | Do instead |
| --- | --- | --- |
| an exception whose base does not end in `Error`/`Exception` (`class Conflict(Problem)`) | not found | a second search for classes whose base is a name the first search found (below) |
| an exception made with `type("DynamicError", (Exception,), {})` | not found | search `type\(\s*["']\w+["']\s*,\s*\(` if the first searches found nothing in a codebase that clearly has errors |
| an exception class defined inside a function | found, indented | read it: a local class is no precedent for a module-level one |
| a public error re-exported from a package `__init__.py` (`from app.pkg._errors import PublicError as PublicError`) | found in `_errors.py` only | read the package's `__init__.py`: a library's public errors are defined in one module and re-exported; the new one follows both steps |
| a functional enum `Enum("Color", "RED GREEN")` | not found | search `Enum\(\s*["']` |
| a lower-case module value (`limit = 10`) | not found | intended: by convention it is not a constant |
| providers searched as `def get_\w+\(` | also finds routes and queries named `get_*` (circular's `get_member`, crud's `get_project`) | always start providers from `Depends\(` and locate each name |
| an upper-case module-level dict or list (`MEMBERS: dict[int, Member] = {}`) | found as a constant | read it: mutable module state is not a constant, and not a precedent for one |

The second search, with the class names the first one found filled in:

```
^\s*class\s+\w+\(\s*(Problem|AppError)\b
```

The lab ran these searches over both recipes and fifteen sandboxes:
every precedent the evals rely on was found (`app/billing/errors.py`,
`app/customers/errors.py` and `app/core/errors.py` in errors-precedent;
`app/errors.py` in credit-limit; `app/listing.py`'s constants and
`app/settings.py`'s `BaseSettings` in constant-or-setting; `app/utils.py`
as the only grab bag in utils-dump), and no-precedent showed no
exception class at all.

## Never

- Never define a thing where it is first used when the codebase keeps its
  kind elsewhere (L10). The router then imports it from the service.
- Never start a second home for a kind that has one.
- Never decide from a file's name alone: `models.py` may hold schemas,
  `errors.py` may be empty. Read the hit.
