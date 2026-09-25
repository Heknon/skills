# Updating docs after a code change

**What it decides:** which pages and docstrings a code change makes
wrong, and what to change in each.

Docs go wrong one change at a time. Every name the change touched can be
written somewhere else: in this repository, in another repository's
docs, or on the combined site.

## Steps

1. **Get the change.** The commits or the diff you were given, or:

   ```powershell
   git diff --stat main...HEAD
   git diff main...HEAD -- "*.py" pyproject.toml
   ```

2. **List what changed that a reader can see.** From the diff: every
   surface (`python/surfaces.md`) added, removed or renamed; every
   default or limit whose value changed; every public function whose
   parameters, return or exceptions changed. Write each as
   `old -> new`, with the old name or value exactly as it was.
3. **Search for each old name and old value.** In the docs folder and
   README of this repository, in docstrings, and, when Sourcegraph is
   connected, across all repositories (`keyword_search` with the exact
   name). Every hit is a page to check.
4. **Fix each hit.** Change the sentence to what the new code does, read
   from the new code. A removed surface: remove it from the page, or say
   in which version it was removed if the page lists versions.
5. **Document what was added** only if it is a surface (the Audit's
   rule), in the page of the right kind.
6. **Docstrings of the changed functions**: check each still holds
   (`python/docstrings.md`).
7. **Changelog**: if the repository keeps one, add the entry in its
   format.
8. **Build strict** (`mkdocs/site.md`).

## Never

- Never update only the page you were pointed at. Search for every old
  name.
- Never describe the change in a reference or how-to ("now retries five
  times", "was changed to"). Pages state what is true now; history goes
  in the changelog.
