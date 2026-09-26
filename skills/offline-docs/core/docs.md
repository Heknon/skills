# Docs: finding written documentation, and its version

**Verdict you produce:** the page or file that documents the thing, and
which version it describes, compared with the installed version.

```
page:      <URL or path>
describes: <dist> <version>, from <where the page says so>
installed: <dist> <version>
use:       as the answer (versions match) | as a lead, checked in the code (they differ or unknown)
```

Pin the installed version first (`core/pin-version.md`).

## What written documentation can be on or near the machine

| Source | Where | Its version |
| --- | --- | --- |
| docstrings of the installed code | `python/pydoc.md` | the installed one, but the text may be stale (`core/behaviour.md`) |
| the README in `METADATA` | `<dist>.dist-info\METADATA` (`python/metadata.md`) | the installed one; orjson 3.12.0's is 1108 lines with every option explained |
| an HTML page written by pydoc | `python -m pydoc -w <module>` (`python/pydoc.md`) | the installed one |
| a doc build on the internal index (devpi) | `<index>/<user>/<index>/<project>/<version>/+doc/index.html` | in the URL and the page |
| a vendored or internal Sphinx or MkDocs site | a folder in a repository, a file share, an internal web server the person names | inside the page (below) |
| Python's own manuals | none known; the standard library source in the interpreter's `Lib\` folder, and `python -m pydoc <topic>` (`tools/cli-help.md`) | the interpreter's |

## Internal pages over HTTP

Read pages only from hosts the person names or from the index the
project already uses (decision OD2), and only with read requests. Find
that index: `[[tool.uv.index]]` in `pyproject.toml`, a `uv.toml`, or the
environment variables `uv help --no-pager run` lists for its index
options: `UV_DEFAULT_INDEX`, `UV_INDEX`, `UV_INDEX_URL` (deprecated form),
`UV_FIND_LINKS` (*lab*, uv 0.12.19). Index settings belong to the
packaging skill; only read them here.

In PowerShell, `Invoke-WebRequest` or `curl.exe` fetch a page (not run on
Windows; the lab used `curl`).

### devpi (lab: devpi-server 6.20.3 with devpi-web 5.1.1)

With docs uploaded for fetchkit 1.5.0 to the index `root/dev`:

| URL | Gave |
| --- | --- |
| `/root/dev/fetchkit/1.5.0/+doc/index.html` | the Sphinx page itself: `<title>fetchkit &#8212; fetchkit 1.5.0 documentation</title>` |
| `/root/dev/fetchkit/latest/+doc/index.html`, `.../stable/+doc/...` | the same page (1.5.0 was the only version uploaded); the URL does not say which version |
| `/root/dev/fetchkit/1.5.0/+d/index.html` | devpi's frame around it (`fetchkit-1.5.0 Documentation`) |
| `/root/dev/fetchkit/9.9.9/+doc/index.html` | 404: no docs for that version |
| `/root/dev/+simple/fetchkit/` | the file list pip and uv read, with links to each wheel and sdist |
| `/root/dev/fetchkit/1.5.0` with the header `Accept: application/json` | metadata and `+links` to the release file and the `doczip` |
| `/+search?query=timeout` | a search over the uploaded pages |

Prefer the URL with the installed version in it over `latest`. Nexus and
other servers were not run; ask the person for the page's address.

## Which version a page describes

- **Sphinx**: the title reads `<project> <release> documentation`, and
  `_static/documentation_options.js` holds `VERSION: '1.5.0',` (*lab*,
  Sphinx 9.1.0).
- **devpi**: the version is in the URL; `latest` is not the installed one
  unless you checked.
- **Anything else**: look for a version in the title, the footer, or a
  "changelog" page's newest entry. If none, the page's version is unknown.

## Steps

1. Look on the machine first: the docstring, the `METADATA` text, the
   stub. These describe the installed version.
2. For more, find the internal page, from the person or the index.
3. Read the version the page describes. Compare it with the installed
   one.
4. Same version: the page can answer, and the verdict is `confirmed from
   page only (<URL>, <version>)` unless you also read the code.
   Different or unknown: the page is a lead; check the claim in the
   installed code (`core/behaviour.md`) and say that the page describes
   another version.

## Never

- Never use a page for another version as the answer.
- Never fetch from a host the person did not name or the project does not
  already use, and never send anything but read requests.
- Never treat the absence of a page as the absence of a feature; look in
  the code (`core/discover.md`).
