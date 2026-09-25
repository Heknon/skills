# Aggregation: one site from several repositories

**What it decides:** how the combined site gets each repository's pages,
why a page or link is missing from it, and how to keep it working after
the move to Zensical.

Each repository keeps its docs in its own `docs\` folder, next to its
code. A separate site repository combines them into one site. There are
three common ways to combine them. Find which one the site uses before
changing anything; each breaks in its own way. All three were built and
tested with MkDocs 1.6.1, Material 9.7.7 and Zensical 0.0.65.

## Step 1: find the style

Read the site repository's `mkdocs.yml`, then search it and its scripts
and CI files.

| You find | Style |
| --- | --- |
| `monorepo` under `plugins:`, and `nav:` entries like `'!include ../billing/mkdocs.yml'` | **A. monorepo plugin** |
| `multirepo` under `plugins:`, and `nav:` entries like `'!import https://git.example/billing?branch=main'`, or a `repos:` list under the plugin | **B. multirepo plugin** |
| a script or CI step that copies folders into `docs\` (`copytree`, `Copy-Item`, `robocopy`, `xcopy`, `cp -r`), or a `.gitmodules` file whose paths are under `docs\` | **C. copy step** |
| `.readthedocs.yaml` | Read the Docs builds it. That service needs the internet; in this network it is usually replaced by one of the three. Ask which runs today. |

If you find none, say so and ask how the site gets the other
repositories' pages. Do not guess.

## A. monorepo plugin

**How it works.** Each `!include` points at another repository's own
`mkdocs.yml`, on disk, relative to the site's `mkdocs.yml`. So every
repository must be checked out next to the site repository before the
build. The plugin reads that repository's `site_name` and `nav:`. Its
pages appear under a folder named from its `site_name`, lowercased with
spaces as dashes: `site_name: Orders Service` gives `/orders-service/`.

**How it breaks.**

- A checkout is missing or at another path: the build fails naming the
  `mkdocs.yml` it cannot find.
- A repository changes its `site_name`: every address under it changes,
  and links from other pages break.
- A page is missing from the repository's own `nav:`: it is built but
  not in the menu. Only `validation: nav: omitted_files: warn` makes the
  strict build fail on it (`site.md`).
- **Zensical ignores `!include`.** The build warns only `page does not
  exist` for links into the missing pages, and without `--strict` it
  exits 0 with those repositories silently absent.

## B. multirepo plugin

**How it works.** At build time the plugin clones each repository with
`git`, through a `bash` script, keeps only its `docs\` folder and
`mkdocs.yml`, and puts the pages under a folder named from the `nav:`
section title (`Billing` gives `/billing/`). The repository's own `nav:`
is used, and it must have one. On Windows it needs Git for Windows' `bash`
on `PATH`. In this network, the URLs must point at the internal git
server; a `file://` path to a local clone also works.

**How it breaks.**

- The git server is unreachable, `bash` is not on `PATH`, or the branch
  is wrong (the default is `master`; set `?branch=main` if the repository
  uses `main`): the build stops with a git or bash error.
- `keep_docs_dir: true` moves every page one folder deeper
  (`billing/docs/…`), and every `nav:` path in the site breaks.
- A page missing from the repository's `nav:`: as in A.
- **Zensical does not support it**, and the plugin is no longer actively
  developed.

## C. copy step

**How it works.** Before the build, a script copies each repository's
`docs\` into the site's `docs\<name>\`. Then it is one ordinary site. With
awesome-nav, each folder can carry a `.nav.yml`, and a `"*"` entry takes
every page in the folder, so a new page appears in the menu without
editing the site:

```yaml
# docs/.nav.yml in the site repository
nav:
  - Home: index.md
  - billing
  - orders
```

```yaml
# docs/billing/.nav.yml, kept in the billing repository's docs folder
title: Billing
nav:
  - index.md
  - "*"
```

With awesome-nav, `mkdocs.yml` has `- awesome-nav` under `plugins:` and
no `nav:` key.

A copy script, in Python so it runs the same on every machine:

```python
"""Copy each repository's docs folder into this site's docs/<name>/."""
import shutil
from pathlib import Path

HERE = Path(__file__).parent
REPOS = {"billing": HERE.parent / "billing", "orders": HERE.parent / "orders"}

for name, repo in REPOS.items():
    target = HERE / "docs" / name
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(repo / "docs", target)
    print(f"copied {repo / 'docs'} -> {target}")
```

Run it with `uv run --no-sync python collect_docs.py`, then build. The
copied folders are build output: list them in the site's `.gitignore`,
and never edit them; edit the page in its own repository.

**How it breaks.** A repository missing from the script's list; a
repository not checked out; an edit made to a copy, lost at the next
copy.

**It works with MkDocs and Zensical alike**, including mkdocstrings,
Mermaid and awesome-nav. It is the migration path for A and B.

## Links between repositories

A page is written in its own repository, but read in the combined site,
where the folders differ. So:

- **Inside one repository**, link relatively, as usual:
  `[charges](api.md)`. This works in both builds.
- **To another repository's page**, a path through the repositories
  (`../../orders/docs/index.md`) always breaks in the combined site. A
  path through the combined site (`../orders/index.md`) works there, but
  breaks the repository's own build.
- So put links between repositories on the site repository's own pages
  (a system page, the home page), which only exist in the combined site.
  When a repository's page must link to another repository, use the
  combined site's full address, and list it under *Not verified*: no
  build checks a full address.

## Moving to Zensical

1. Find the style (Step 1).
2. **C** already works. Build with `zensical build --strict`, compare
   the page list with the MkDocs build, and replace any `validation:`
   checks with awesome-nav `"*"` entries (`site.md`).
3. **A or B**: add a copy step (C) that fills `docs\<name>\` with the
   same folder names the plugin produced, so addresses do not change;
   move each repository's `nav:` into a `.nav.yml` in its `docs\` folder;
   remove the plugin and the `!include` or `!import` entries; build both
   ways and compare the list of built pages:

   ```powershell
   Get-ChildItem site -Recurse -Filter index.html | ForEach-Object { $_.FullName.Substring((Resolve-Path site).Path.Length) } | Sort-Object
   ```

   The lists must match before the plugin is removed for good.
4. The change touches every repository's docs folder and the site's
   build. It is a large change: ask before starting it, unless you were
   asked for the migration itself.
