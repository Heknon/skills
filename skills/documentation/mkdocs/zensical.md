# Zensical

**What it decides:** whether and how to move a site from MkDocs to
Zensical.

Zensical is the successor to Material for MkDocs, by the same team. It
reads an existing `mkdocs.yml`. Tested at 0.0.65, on 2026-09-25. Versions
before 0.1.0 are previews: do not call them stable. Its first dependable
release, 0.1.0, was due on 2026-11-05.

## Why move, and by when

Material for MkDocs gets critical fixes only until **2027-05-05**, and
MkDocs 1.x gets none. A site that stays on them keeps working, but a
security or compatibility problem after that date will not be fixed.
Moving is the team's decision. Asked "should we", answer with what is at
stake, the dates, and what the move takes; do not answer just yes or no,
and do not start it unasked.

## What carries over, tested at 0.0.65

| Works unchanged | Does not |
| --- | --- |
| `mkdocs.yml`, Material theme settings, `font: false` | the **monorepo** plugin: `!include` is ignored, the pages are missing |
| mkdocstrings and its options | the **multirepo** plugin: not supported |
| pymdownx extensions, Mermaid through `extra_javascript` | `validation:` settings: ignored, so pages left out of `nav:` pass the strict build |
| awesome-nav `.nav.yml` files | |
| `--strict`: fails on a broken link or a missing `:::` object | `griffe:` docstring warnings: printed, but the strict build passes |

Zensical's own list of supported plugins also names search, offline,
blog, tags, autorefs, macros, mike and redirects. Anything else under
`plugins:` must be tried in a build before the move.

## How to move

1. `aggregation.md`, "Moving to Zensical", if the site combines
   repositories.
2. Build with both, from the same `mkdocs.yml`:

   ```powershell
   uv run --no-sync mkdocs build --strict --site-dir site-mkdocs
   uv run --no-sync zensical build --strict
   ```

   Zensical writes to `site\`.
3. Compare the built page lists (the command is in `aggregation.md`). A
   page in the MkDocs list and not in the Zensical one is a plugin that
   did not carry over.
4. Replace `validation: nav: omitted_files` with awesome-nav `"*"`
   entries, so no page falls out of the menu unnoticed.
5. Change the build command in CI and in the README, and pin both
   `mkdocs<2` and the Zensical version in the project file.
