# Locate

**Verdict you produce:** where `X` is defined, as `path:line`, and the
chain of imports that led there from the file that uses it.

```
X is defined at <path:line>: <the definition line>
resolved from <using file:line> -> <each import hop, path:line> -> <definition>
```

## Steps

1. **Start from where `X` is used**, if you were given a place. The
   definition that counts is the one this file's imports lead to, not the
   first one a search finds (invariant 3 in `SKILL.md`).
2. **If Sourcegraph is available** and the repository is indexed there,
   call `go_to_definition` with the repository, the using file's path and
   the symbol (`tools/sourcegraph.md`). Then open the result and confirm it
   (invariant 1). If it returns nothing, continue with step 3.
3. **Read the using file's imports.** Find the line that brings `X` in:
   `from a.b import X`, `from a.b import Y as X`, `import a.b` then
   `a.b.X`, or `from a.b import *`. If there is no import, `X` is defined
   in the same file, is a builtin, or is created dynamically.
4. **Turn the import into a file** with `python/imports.md`. Open it.
5. **Is `X` defined there, or imported there too?** If the file imports
   it again (a re-export, often in an `__init__.py`), go back to step 3
   with this file. Follow the chain until a definition line:
   `def X`, `class X`, `X =`, `X: T =`.
6. **No using file given?** Search with a definition pattern
   (`core/search-patterns.md`). One hit: open it and confirm. Several: list
   them all, and say which one each caller reaches, or ask which caller is
   meant.
7. **Still nothing?** The name may be made at runtime
   (`python/dynamic.md`), come from an installed package (ask the
   interpreter, `tools/terminal-probes.md`), or be a builtin.

## Never

- Never answer with the first search hit when a name is defined more than
  once. Say how many definitions exist and which one the caller reaches.
- Never stop at an `__init__.py` that only imports the name. That is a
  re-export, not a definition.
