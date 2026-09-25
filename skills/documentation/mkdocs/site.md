# Building and checking the site

**What it decides:** whether the site builds, what a build message
means, and how to keep the site working with no internet.

All commands run in PowerShell from the folder that holds `mkdocs.yml`,
through uv, so they use the project's own environment.

## The commands

| Purpose | MkDocs | Zensical |
| --- | --- | --- |
| check everything, fail on any warning | `uv run --no-sync mkdocs build --strict` | `uv run --no-sync zensical build --strict` |
| preview while writing | `uv run --no-sync mkdocs serve` | `uv run --no-sync zensical serve` |

The strict build is the check. Run it after every change to a page, a
docstring shown in the API reference, or `mkdocs.yml`. It exits 1 on a
warning, and prints `Aborted with N warnings in strict mode!` (MkDocs) or
`RuntimeError: Aborted because --strict flag is set` (Zensical).
Without `--strict`, both exit 0 even with broken links.

**Zensical 0.0.65 prints docstring warnings but does not count them.**
Lines starting `griffe:` appear in its output, yet it says `No issues
found` and exits 0, even with `--strict`. Read the output for `griffe:`
lines, or run the MkDocs strict build, which fails on them.

## Make MkDocs report what it hides by default

By default MkDocs only mentions, as `INFO`, a page that exists but is not
in `nav:`, so the strict build passes while the page is unreachable from
the menu. Add this to `mkdocs.yml` so the strict build fails on it:

```yaml
validation:
  nav:
    omitted_files: warn
  links:
    unrecognized_links: warn
    anchors: warn
```

**Zensical 0.0.65 ignores `validation:`.** Under Zensical, a page left out
of an explicit `nav:` is built but reachable only by its address. Use
awesome-nav with a `"*"` entry instead (`aggregation.md`), so new pages
join the menu by themselves.

## Offline: the two things that reach the internet

Tested with Material 9.7.7 and Zensical 0.0.65. Everything else Material
needs is inside the package.

1. **Fonts.** Material loads its fonts from Google Fonts. Turn it off:

   ```yaml
   theme:
     name: material
     font: false
   ```

2. **Mermaid diagrams.** Material loads Mermaid from `unpkg.com` the
   first time a page has a diagram, unless Mermaid is already on the
   page. Keep a copy of `mermaid.min.js` in the docs folder and load it:

   ```yaml
   extra_javascript:
     - javascripts/mermaid.min.js
   markdown_extensions:
     - pymdownx.superfences:
         custom_fences:
           - name: mermaid
             class: mermaid
             format: !!python/name:pymdownx.superfences.fence_code_format
   ```

   The file goes in `docs\javascripts\mermaid.min.js`, copied from the
   team's package mirror. If it is missing, diagrams show as code, and
   the build does not warn.

After a build, search the built site for addresses outside the network:

```powershell
Get-ChildItem site -Recurse -Filter *.html | Select-String -Pattern 'https://' | Select-String -NotMatch 'squidfunk.github.io|zensical.org'
```

The two addresses excluded are footer links to the theme's home page;
they load nothing. Anything else found is a font, script or image the
page will try to fetch.

The theme's own script, `assets\javascripts\bundle.*.min.js`, also
contains `unpkg.com` addresses: one for Mermaid, used only when the page
did not load Mermaid itself, and one for a ResizeObserver polyfill, used
only by browsers too old to have ResizeObserver. With the two fixes
above, neither is fetched. Do not edit the bundle.

## Build messages and what they mean

| Message | Cause | Fix |
| --- | --- | --- |
| `Doc file 'a.md' contains a link 'b.md', but the target is not found among documentation files.` | the link's path is wrong from where `a.md` sits | fix the relative path; after aggregation, paths change (`aggregation.md`) |
| `A reference to 'x.md' is included in the 'nav' configuration, which is not found in the documentation files.` | `nav:` names a page that does not exist at that path | fix the path in `nav:` or restore the page |
| `The following pages exist in the docs directory, but are not included in the "nav" configuration:` | a page is not in the menu | add it to `nav:`, or use awesome-nav with `"*"` |
| `mkdocstrings: x.y.z could not be found` then `Could not collect 'x.y.z'` | the `:::` line names a module or object that does not exist, or `paths:` does not point at the source folder | check the dotted path with navigation, Locate; check `paths:` (`api-reference.md`) |
| `griffe: path.py:7: Parameter 'a' does not appear in the function signature` | a docstring documents a parameter the function does not have | fix the docstring (`python/docstrings.md`); Zensical prints it but passes |
| `griffe: path.py:7: No type or annotation for parameter 'a'` | usually the line above: the documented name is not a real parameter | same |
| `Zensical: page does not exist` | a link's target does not exist | fix the link |
| `Warning from the Material for MkDocs team` in a red box | Material's notice about MkDocs 2.0 | not an error; nothing to fix |

## Never

- Never pass a strict build by turning off a check, lowering a
  `validation:` level, or removing `--strict` from a command or CI file.
- Never add a CDN address (`unpkg.com`, `cdn.jsdelivr.net`, Google Fonts)
  to the config.
