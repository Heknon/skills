# MkDocs: where things stand, and which file to read

**Read this first for any Site task.** You cannot look any of this up.
The facts below were checked on **2026-09-25**. If a version you find
installed is newer than the ones named here, say so in your answer: the
facts may have moved.

## The state of the tools on 2026-09-25

| Tool | State | What it means for you |
| --- | --- | --- |
| **MkDocs 1.6.1** | the last 1.x release; no release in about 18 months | works; fixes will not come |
| **MkDocs 2.0** | pre-release; removes plugins, config moves to TOML, breaks Material | never install it; every project pins `mkdocs<2` |
| **Material for MkDocs 9.7.x** | maintenance; end of life 2026-11-05, critical fixes until **2027-05-05**; 9.7.5 and later pin `mkdocs<2` | works; prints a red warning box about MkDocs 2.0 on every build, which is not an error |
| **Zensical** | successor by the Material team; reads `mkdocs.yml`; tested at 0.0.65; 0.1.0 due 2026-11-05 | the migration target; see `zensical.md` |
| **mkdocstrings 1.0 + mkdocstrings-python 2.0** (griffe underneath) | maintained; works with MkDocs and Zensical | API reference from docstrings; see `api-reference.md` |
| **mkdocs-monorepo-plugin 1.1.2** | maintained by the Backstage team; **Zensical ignores it** | see `aggregation.md` |
| **mkdocs-multirepo-plugin 0.8.3** | no longer actively developed; **not supported by Zensical** | see `aggregation.md` |
| **mkdocs-awesome-nav 3.3.0** | maintained; works with MkDocs and Zensical | navigation from `.nav.yml` files |

## Read the installed versions

Run from the folder that holds `mkdocs.yml`:

```powershell
uv pip list --offline | Select-String -Pattern "mkdocs|zensical|griffe|pymdown"
```

Plugins in use are the names under `plugins:` in `mkdocs.yml`. The
package for a plugin name is usually `mkdocs-<name>-plugin` or
`mkdocs-<name>`; `uv pip show <package>` confirms it.

## Which file next

| You need to | Read |
| --- | --- |
| build, check, serve, fix a build error, keep it offline | `site.md` |
| combine several repositories into one site; pages missing from the combined site; links broken between repositories | `aggregation.md` |
| show API reference from docstrings | `api-reference.md` |
| move from MkDocs to Zensical, or decide whether to | `zensical.md` |
| plan a move to Read the Docs, or decide whether it can work here | `read-the-docs.md` |

## Never

- Never upgrade to MkDocs 2.0, and never remove a `mkdocs<2` pin.
- Never add a plugin, theme or package without being asked. A new
  package must come from the team's package mirror, and someone must
  approve the dependency. Propose it in *Not done* instead.
