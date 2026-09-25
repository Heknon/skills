# Plan: the offline-docs skill

Status: draft for decision. Nothing is built yet.

## 1. What it is

How to find answers with no web access. It answers "how does this
library or tool work, what does this function accept, what changed in
this version" from what is on the machine: the installed source in
`site-packages`, `help()` and `pydoc`, `inspect`, `importlib.metadata`
and the `*.dist-info` folder, type stubs, a tool's own `--help`, and
internal mirrors of documentation. Every answer is stamped with the
version it was checked on and ends in a verdict:

```
Answer:   <one or two lines>
Checked:  <distribution> <version>, Python <x.y.z>, <interpreter path>
Evidence: <path:line and what is there> | <command and the line it printed>
Source:   code | stub | docstring | --help | metadata | internal page
Verdict:  confirmed from source at path:line on <version>
          | confirmed from <stub, help, page> only | not found (<where looked>)
```

It carries knowledge and judgement, not enforcement. Memory of a
library is where a search starts, never the answer.

## 2. The environment it is written for

A weak model in Zed's agent on Windows with PowerShell, air gapped,
Python through uv (`uv run --no-sync`), packages only from an internal
mirror, no web. Its memory is of some version, often not the installed
one. `help()` may wait in a pager in Zed's terminal (to verify in the
lab), so docs are printed with `pydoc.render_doc(obj,
renderer=pydoc.plaintext)`, single quotes only inside `python -c "..."`.

What documentation can exist offline:

| Source | What it gives | Caveat |
| --- | --- | --- |
| installed source in `site-packages`, stdlib in the interpreter's `Lib\`; `inspect.signature`, `getsource` | the code that runs, the real parameters | compiled modules have none; `signature` follows `__wrapped__` |
| docstrings: `render_doc`, `pydoc -w` (HTML file), `pydoc -p 0` (local server), `pydoc -k` | the author's description | can be stale; importing runs code; `-p` may raise a firewall prompt (to verify) |
| `*.dist-info`: `METADATA`, `entry_points.txt`, `RECORD`, `direct_url.json`, `INSTALLER` | version, dependencies, often the README, every installed file, editable or not | `METADATA` prose is for the release, not a guarantee |
| stubs: inline `.pyi`, `types-*` packages, typeshed inside mypy and pyright | signatures of compiled or untyped code | may be for another version |
| CHANGELOG or NEWS; else a second version from the mirror in a throwaway environment | what changed; a diff of two sources | changelogs are rare in wheels, commoner in sdists (to verify) |
| `--help`, `uv help`, `ruff rule`, `ruff config`, `git <cmd> -h`, `Get-Help` | the tool's own account | from the binary that runs; no `man` on Windows; `git help` opens HTML; full `Get-Help` needs `Update-Help` (to verify) |
| internal doc mirrors: devpi `+doc`, Nexus raw sites, vendored Sphinx or MkDocs builds | written documentation | for some version, often not the installed one |

## 3. The kinds of task

| Kind | Asked to | Answer shape |
| --- | --- | --- |
| **Version** | say which version of X is installed and where from | distribution, version, location, installer, editable or copy |
| **Signature** | say what a function or class accepts and returns | the signature, the `def` as path:line, where `**kwargs` goes |
| **Behaviour** | say what X does in a case (default, error, `None`) | the lines of code that decide it, path:line, and the verdict |
| **Changed** | say what changed between versions, or since when X exists or is deprecated | evidence per version: changelog lines, or a diff of the two installed sources |
| **Discover** | find which function, class or option does Y | candidate names, each path:line, from `__all__`, `pydoc -k`, a search in the package |
| **Tool** | explain a CLI flag, rule or setting | the tool's own output line, and the tool's version and path |
| **Docs** | find the documentation for X | the page or file, and which version it describes |

Each kind starts with the same first step: pin the interpreter and the
distribution version (`core/pin-version.md`). Nothing is read before it.

## 4. The failures it targets

| Failure | What it looks like |
| --- | --- |
| **Memory for the wrong version** | answers `model_dump()` where pydantic 1.10 is installed, or a flag added after the installed release |
| **Repository source, not installed** | reads a vendored copy, a checkout in the repository or another venv, while `site-packages` holds another version |
| **Docstring over code** | the docstring says "defaults to 3 retries", the code says `retries=0`; the model reports 3 |
| **Invented keyword** | passes `verify_ssl=True` because `**kwargs` "accepts anything", or a keyword from another version |
| **Wrapper signature** | reports `(*args, **kwargs)` of a decorator, or trusts `__wrapped__` when the wrapper changes the arguments |
| **Stub over runtime** | a `types-*` stub or bundled typeshed lists a parameter the installed version lacks |
| **Wrong binary** | `ruff --help` from a global install on `PATH`, not `uv run ruff` of the project |
| **Invented changelog** | "in 2.0 they renamed X" with no changelog or diff behind it |
| **Silent not-found** | one search finds nothing, so the model invents an option instead of saying "not found" |
| **Stuck or side effects** | `help()` waits in a pager; `pydoc` imports a module that connects to a database |

## 5. Layout

```
skills/offline-docs/
  SKILL.md          router over the seven kinds, invariants, answer shape
  glossary.md       distribution vs import name, sdist, dist-info, stub
  core/
    pin-version.md  first step: interpreter, distribution, version, location
    signature.md    signature, def line, following **kwargs to where they land
    behaviour.md    read the code path for one case; a docstring is a lead
    changed.md      changelog, else uv run --isolated --with pkg==X and diff
    discover.md     __all__, dir(), pydoc -k, a search in one package folder
    tool.md         asking a CLI about itself, from the binary that runs
    docs.md         internal doc mirrors, pydoc HTML; stating their version
    evidence.md     ranking of sources; how to write "not found"
  python/
    installed-files.md  RECORD, __file__, .pyd files, the stdlib's Lib\
    pydoc.md        render_doc without a pager, -w, -p, -k; imports run code
    inspect.md      signature, getsource, __wrapped__, no-signature builtins
    metadata.md     importlib.metadata, packages_distributions(), dist-info
    stubs.md        inline .pyi, py.typed, types-* packages, bundled typeshed
  tools/
    cli-help.md     --help, uv help, ruff rule, git -h; no man; Get-Help
  examples/         three worked lookups; evals/: evals.json and sandboxes
```

## 6. Dependencies and boundaries

From the roadmap:

| Skill | Needs | Relies on by name | Existing skills it touches |
| --- | --- | --- | --- |
| offline-docs | none | none | navigation |

| Ground | Owner | The other side |
| --- | --- | --- |
| looking things up in installed packages and the environment | offline-docs | navigation keeps finding code in the repository and which interpreter runs it |

**Needs none**: it teaches Python, uv and the tools themselves; wave 1.
**Relied on by name** by debugging, pydantic, packaging and api, which
point here for "check it in the installed version".

**The line with navigation.** navigation answers "where is this in our
code" and owns its Environment question: which interpreter runs,
`sys.path`, editable vs copy. offline-docs answers "what does a library
or tool do", starting from that interpreter. It repeats one uv probe
(`import x; print(x.__version__, x.__file__)`) and sends anything
unusual (poetry, conda, a stray `python`) to navigation. navigation's
search rules exclude `site-packages`; offline-docs searches there on
purpose, inside one package. navigation's `tools/terminal-probes.md`
keeps `inspect.signature`, `importlib.metadata.version` and console
scripts for project code; offline-docs owns third-party code: wrappers,
compiled modules, stubs as signatures, `**kwargs`, dist-info, versions
compared. navigation's `python/types.md` keeps stubs as a type source.

Other edges: linting owns what ruff, mypy and pyright output means,
offline-docs only how to ask a tool; packaging owns how dist-info and
entry points are built, offline-docs only reads them.

### Proposed changes to the roadmap

1. Boundary row: "and the environment" reads as if offline-docs owned
   it. Proposed: "looking things up in installed packages and tools |
   offline-docs | navigation finds code in the repository and owns which
   interpreter runs it".
2. Dependencies row: "Relies on by name" becomes `navigation`, not
   `none`. "Needs" stays `none`.
3. New boundary row: "a checker's `--help` and `ruff rule` output |
   linting owns what it means | offline-docs owns how to ask".

## 7. How it will be verified

- **Versions.** Python 3.12, as in pytest; uv, ruff, mypy, pyright, ty
  and git for Windows at the mirror's versions on the lab day, recorded.
  Libraries follow R2. Real packages: pydantic and pydantic-core
  (compiled, `.pyi`), orjson (compiled, stubs only), requests (`**kwargs`
  passed on). Each on the mirror: to verify.
- **Where.** Windows 11, PowerShell 5.1 and 7, uv, in Zed's agent
  terminal, no network but the mirror.
- **What the lab must run.** Every command in the skill, its output
  copied into the file that states it. In particular: whether `help()`
  and `python -m pydoc x` block in Zed's terminal; where `pydoc -w`
  writes; `inspect.signature` on compiled and decorated functions;
  what a uv-managed Python ships in `Lib\`; that `uv run --isolated
  --with pkg==X` leaves `.venv` unchanged; how many of the mirror's top
  50 packages ship a changelog; `git help` and `Get-Help` offline. Each
  eval bait is reproduced on MiniMax 2.7 without the skill first.

## 8. Evals, written first

Toy libraries are built as wheels in the lab and shipped in the sandbox
as a wheelhouse (`uv pip install --find-links wheels`); `old-pydantic`
and `compiled-stub` copy real wheels from the mirror into theirs.

| Sandbox | Task | Bait |
| --- | --- | --- |
| `old-pydantic` | "dump this model to a dict without unset fields" | pydantic 1.10 installed (on the mirror: to verify); memory says `model_dump` |
| `vendored-copy` | "what is `fetchkit.get`'s default timeout?" | `third_party/fetchkit/` in the repository is 1.2 (30 s); installed 2.0 has `None` |
| `stale-docstring` | "how many times does `retry_call` retry by default?" | docstring says 3; code says 0 |
| `kwargs-passthrough` | "turn off SSL checks on this call" | `get(url, **kw)` forwards to `_send(headers, timeout)`; no SSL keyword exists |
| `compiled-stub` | "what does `orjson.dumps` accept?" | `getsource` fails (to verify); the answer is the `.pyi`, stated as stub only |
| `stub-mismatch` | "can I pass `retries=` to `fetchkit.get`?" | an installed `types-fetchkit` lists it; runtime 2.0 does not |
| `what-changed` | "what changed from `fetchkit` 1.4 to 1.5 that breaks our call?" | no changelog in the wheels, one in the 1.5 sdist; the model invents one |
| `wrong-ruff` | "does our ruff have rule `<code>`?" | the project's ruff has it; an older `ruff.exe` first on `PATH` does not (how to place it: to verify) |
| `no-such-option` | "which setting makes `quickcfg` read YAML?" | none exists; the right verdict is "not found" and where it looked |

Graded by hand: version stamped, evidence at path:line in
`site-packages`, source kind named, "not found" when it is true.

## 9. Decisions needed

### R1. Its own skill, or a folder of navigation

*For a folder:* navigation has the probes and the Environment question
every lookup starts from; no duplication, one skill less to load.
*For its own skill:* the question differs ("how does this library work"
vs "where is this in our code"); navigation's rules point the other way
(exclude `site-packages`, repository locations, no version stamp); half
the sources are not code (`--help`, dist-info, changelogs, doc mirrors);
four domain skills must point at it without loading an eight-question
router; and "what does this function accept" does not match
navigation's description, so navigation would not load for it.
*Recommended:* its own skill, small, starting from navigation's
Environment verdict. Nothing moves out of navigation; it gains one
pointer line in `tools/terminal-probes.md`.

### OD1. Scope

*Recommended:* Python packages and the standard library, plus asking
any CLI about itself. No other languages. Is there a copy of Python's
own docs (CHM, an internal Sphinx build)? Until one is named, the
standard library source in `Lib\` is the reference.

### OD2. Fetching internal documentation pages

May the model read pages over HTTP (`Invoke-RestMethod`, `curl.exe`)
from a devpi or Nexus docs host, and which? *Recommended:* yes, read
only, from hosts the person names or the index in `uv.toml`; a page
ranks below the installed source unless it names the installed version.

### OD3. A throwaway environment for another version

`uv run --isolated --with pkg==X` downloads into uv's cache and leaves
the project alone. *Recommended:* allowed for Changed questions and
said in the answer; never `uv add` or `uv sync`.
