# Trace in

**Verdict you produce:** every place that calls or uses `X`, each as
`path:line`, and whether it is safe to change or remove `X`.

```
uses: <path:line - how it is used: call, import, registration, string, subclass>
safe to change: <yes | no, because <use> | unknown, because <what could not be searched>>
```

## Steps

1. **Locate `X` first** (`core/locate.md`). You need its module path and
   its exact name, and whether it is exported.
2. **If Sourcegraph is available**, call `find_references` on the
   definition, with a `limit` high enough (the default is 10). It finds
   uses across every indexed repository. Confirm a few by reading them,
   then continue with step 4; it does not find dynamic uses.
3. **Search the project** with the use patterns in
   `core/search-patterns.md`: calls, attribute access, and imports of `X`.
   For each file that imports `X` under another name (`import X as Y`),
   search that file for `Y` too.
4. **Go through `core/what-search-misses.md`**, all eleven items. Each
   one that applies is either searched and ruled out, or listed under *Not
   covered*.
5. **Read every hit.** Mark each one: call, import only (unused import),
   registration, string reference, subclass or override, test, comment.
   Comments and dead imports are not uses.
6. **Decide safety.** No uses after steps 2 to 5, and nothing left under
   *Not covered*: safe. Any use: not safe, name it. Anything not covered,
   such as other repositories without Sourcegraph: unknown, say what.

## Never

- Never write "unused" from one search for `X(`.
- Never count a test as the only user without saying so; code used only
  by tests is a finding in itself.
