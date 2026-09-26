# Search patterns

**What it decides:** how to write a search that finds what you mean.

A search for a bare name returns every line that contains those letters:
the definition, every call, every import, comments, strings, and other
things that happen to share the name. Finding the right one among them is
where weak searching goes wrong. Search for the shape of the thing, not
the name alone.

## Definitions in Python

Regular expressions for the editor's `grep` tool. They use Rust regex
syntax: no lookbehind, no backreferences. `\b` is a word boundary.

| Looking for | Pattern |
| --- | --- |
| a function or method `load` | `^\s*(async\s+)?def\s+load\b` |
| a class `Client` | `^\s*class\s+Client\b` |
| a module-level name `TIMEOUT` assigned | `^TIMEOUT\s*(:[^=]+)?=` |
| a name set inside a class or function | `^\s+TIMEOUT\s*(:[^=]+)?=` |
| an attribute set on instances | `self\.timeout\s*=` |
| an import of `Client` | `import\s+.*\bClient\b` |
| a re-export in an `__all__` | `__all__.*["']Client["']` |
| a decorator named `route` | `^\s*@[\w.]*\broute\b` |

An import of module `billing`, in any form, `from app import billing`
included (a pipe inside a table cannot be shown safely, so it is here):

```
^\s*(from|import)\s+[\w.]*\bbilling\b|^\s*from\s+[\w.]+\s+import\s+.*\bbilling\b
```

An import in parentheses over several lines is missed; widen to the bare
name (rule 3).

## Uses in Python

| Looking for | Pattern |
| --- | --- |
| calls of `load` | `\bload\s*\(` |
| attribute access `.load` | `\.load\b` |
| the name as a string | `["']load["']` |
| a dotted path as a string | `["'][\w.]*\bload\b` |
| keyword argument `timeout=` | `\btimeout\s*=` without `self.` in front |

## Rules

1. **Filter by file type.** Restrict to `**/*.py` unless you are looking
   for a string that may be in configuration: then add `*.toml`, `*.cfg`,
   `*.ini`, `*.yaml`, `*.yml`, `*.json`, `*.env`.
2. **Exclude what is not source.** `.venv`, `venv`, `site-packages`,
   `build`, `dist`, `__pycache__`, `.git`, `node_modules`. A hit there is
   installed or generated code; it matters only for an Environment
   question.
3. **Start narrow, widen once.** A definition pattern first. If it finds
   nothing, the name may be created dynamically (`python/dynamic.md`) or
   imported under another name (`core/resolve.md`); widen to the bare name
   only then.
4. **Too many hits: add a boundary, not a guess.** Add `\b`, the file
   filter, or the containing folder. Never pick "the most likely" of
   thirty hits without reading.
5. **Case matters in Python.** Search case-sensitively for names.
6. **Escape what regex treats as special** when searching literal text:
   `.` `(` `)` `[` `]` `{` `}` `?` `*` `+` `|` `^` `$` `\`.

## Never

- Never report a hit as a definition without reading the line.
- Never conclude from a search inside `.venv` or `site-packages` what the
  project's own code does.
