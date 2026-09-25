# Finding gaps

**What it decides:** what in the docs is undocumented, wrong, stale,
duplicated or unreachable, and which to fix first.

An Audit reports; it does not fix, unless the ask says to. Each finding
comes with its evidence, so a person can act on it without redoing your
search.

## The six checks

Run them in this order. Keep a list as you go.

1. **Undocumented surfaces.** List the surfaces (`python/surfaces.md`).
   For each exact name, search the docs folders and the README. Record
   documented, mentioned, or undocumented.
2. **Wrong claims.** For each number, default, name, command and path a
   page states, find it in the code (`core/claims.md`). A value that
   differs is wrong. A name that no longer exists is wrong.
3. **Stale pages.** For each page, compare when it and the code it
   describes last changed:

   ```powershell
   git log -1 --format="%cs %h" -- docs/how-to/charge.md
   git log -1 --format="%cs %h" -- src/billing/charges.py
   ```

   Code changed after the page: check that page's claims (check 2). A
   page that is older is not wrong by itself; only a claim that no longer
   holds is.
4. **Duplicated facts.** Search the docs for each distinctive value you
   met in check 2 (a number, an option, an address). The same fact on two
   pages is a finding, even when both agree today.
5. **Unreachable pages.** A page in no `nav:` and linked from no page.
   The MkDocs strict build with `validation:` lists pages missing from
   the menu (`mkdocs/site.md`). For links, search the docs for the page's
   file name.
6. **Public code with no docstring.** It is missing from the API
   reference without a warning (`mkdocs/api-reference.md`). Search each
   public module for `def ` and `class ` lines with no docstring under
   them.

## Order of the findings

1. **Wrong**: readers act on it today.
2. **Undocumented surfaces** someone outside must use: commands, options,
   environment variables, settings, routes.
3. **Stale** pages with a claim that no longer holds.
4. **Duplicated** facts.
5. **Unreachable** pages.
6. **Missing docstrings** on public code.

## The report

One table, in that order:

| # | Finding | Kind | Where | Evidence | Fix |
| --- | --- | --- | --- | --- | --- |
| 1 | README says 3 retries; code says 5 | wrong | `README.md:14` | `src/billing/charges.py:9` `retries: int = 5` | change the README to 5, or link to the reference |

Then the *Not done* heading lists what you could not check (for example,
repositories you could not reach).

## Never

- Never report a gap you did not search for. "Probably undocumented" is
  not a finding.
- Never count a name that only appears in a code block as documented.
  It is mentioned.
