# Resolve

**Verdict you produce:** what a name, an import or a type really refers
to, and the rule that decided it.

```
<name or import> at <path:line> resolves to <path:line of the definition>
by: <the rule, such as "relative import from package app.api", "re-export in app/api/__init__.py:3", "installed package in .venv, not the repository copy">
type (if asked): <type> from <checker> (<its output line>)
```

## Three kinds of question

1. **An import**: which file does `from x.y import z` load? Use
   `python/imports.md`. When the answer matters, confirm with the
   interpreter: `tools/terminal-probes.md`, "where a module comes from".
2. **A name in a file**: a local, a parameter, an import, a module-level
   name, a builtin, or an attribute set elsewhere. Read the enclosing
   function and the file's imports, in that order.
3. **A type**: `python/types.md`. Annotations first, then a checker's
   `reveal_type`, then the runtime.

## When the repository and the interpreter disagree

The file you read in the repository may not be the one that runs: an
installed copy in the virtual environment, an older build, a same-named
module earlier on `sys.path`, or a different interpreter. When behaviour
does not match the source, resolve with the interpreter, not with search.
This is the most common reason "I changed it and nothing happened".

## Never

- Never resolve an import by picking a file with the right name from a
  search. Apply the import rules, then confirm.
