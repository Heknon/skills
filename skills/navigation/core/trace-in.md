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
   On a branch that will merge into another, search that branch too:
   callers it gained after your branch point are not in your files.
   ```
   git fetch
   git grep -n -w X origin/main
   ```
   Each hit is `origin/main:path:line:text`. *lab* (git 2.43.0): on
   the feature branch, `git grep -n -w get_user` missed `report.py`,
   which main had added since; the command above found
   `origin/main:report.py:4:    return get_user(2)`.
4. **Go through `core/what-search-misses.md`**, all eleven items. Each
   one that applies is either searched and ruled out, or listed under *Not
   covered*.
5. **Read every hit.** Mark each one: call, import only (unused import),
   registration, string reference, subclass or override, test, comment.
   Comments and dead imports are not uses.
6. **Follow each use back to where it can be reached from.** A use inside
   a function that nothing in this repository calls is not the end: ask
   what can reach that function from outside. It is reachable when it is
   public (no leading underscore, in a module others can import), when it
   is an entry point (`python/entry-points.md`), or when the use depends
   on outside data: a dispatch keyed by a message's field, a request's
   path, a file's content, a setting. Outside data can bring any key, so
   a handler registered for that key is live even if no line in this
   repository sends it.
7. **Decide safety.** No uses after steps 2 to 6, and nothing left under
   *Not covered*: safe. Any use reachable as in step 6: not safe, name
   the use and how it is reached. Anything not covered, such as other
   repositories without Sourcegraph: unknown, say what.

## Never

- Never write "unused" from one search for `X(`.
- Never count a test as the only user without saying so; code used only
  by tests is a finding in itself.
- Never call something dead because the only function that reaches it is
  itself not called in this repository. Public functions, entry points
  and dispatch on outside data are reached from outside it.
