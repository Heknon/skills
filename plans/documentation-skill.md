# Plan: the documentation skill

Status: draft for decision. Nothing is built yet.

## 1. What the skill must do

Give a weak, offline model (the target is MiniMax 2.7 class) the ability to:

1. **Write** documentation that is accurate, sourced, and shaped for its reader.
2. **Find** what is undocumented, what is stale, and what is wrong, and
   document it.
3. **Structure** documentation: one repository, one system with many
   subsystems, a monorepo, a system spread over many repositories, and a
   team that owns many systems.
4. **Keep it true** as the code changes.
5. **Choose and run the tooling**: which site generator, reference
   generator, diagram tool, linter, link checker and search to use for which
   problem, and how to install and run each one without internet.

**Air gapped is a hard constraint.** The model cannot search the web, and
neither can the tools. Every fact the model needs about a tool, such as its
config keys, commands, plugin names and failure modes, is written into the
skill and stamped with the version it was verified against, as the backends
are in observability. Every recommended tool must build and serve with no
network: no CDN scripts, no remote fonts, no hosted search, no plugin that
calls home. A tool that cannot do that is documented as unsuitable, with the
reason.

The skill does the thinking in advance, as the observability skill does. The
model follows procedures, fills templates and runs checkers. It does not
design a documentation structure from principles, and it does not state a
fact about the code that it cannot point at.

## 2. What we carry over from the observability skill

These worked. The weak-model eval run on observability is the evidence
(`skills/observability/evals/evals.json`, `runs`).

| Observability | Documentation equivalent |
| --- | --- |
| Router over six task kinds, load only what the task needs | Router over six task kinds (section 4) |
| Procedures: verdict first, numbered factual questions, verdict block, never list, stop and ask | Same shape, unchanged |
| `vocabulary.md` in the project is law | `docs-map.md` in the project is law (section 5) |
| Invariants a procedure never overrides | Documentation invariants (section 6) |
| Four fixed answer headings, so invention has nowhere to hide | Five fixed answer headings (section 7) |
| `checks/` scripts, Python 3.11 standard library, fixtures, `run_fixtures.sh` | Same, over pages, maps, links, claims and coverage (section 9) |
| `backends/`: same file names per backend, a selector README, a choosing procedure | `tooling/`: same file names per tool, a selector README, a choosing procedure (section 10a) |
| Worked examples whose golden data passes the checkers | Worked examples whose golden docs pass the checkers (section 11) |
| `glossary.md` fixes the words, no synonyms | Same |
| `evals/` with a "never open this while doing a task" rule | Same |

The lesson from the observability eval run that matters most here: asked to
"just pick a good name", the model invented one. In documentation the same
failure is inventing behaviour, defaults and rationale. The design below is
built around stopping that.

## 3. Three established models, not our own

A weak model follows a structure well when the structure is fixed and
well known. We adopt three existing models and write procedures over them
instead of inventing a taxonomy.

| Question | Model adopted | Why |
| --- | --- | --- |
| What kinds of thing exist in an organisation's software, and how do they nest | **Backstage catalog kinds**: Group (team), Domain, System, Component, API, Resource | A published, widely used ontology for exactly "a team has systems, systems have subsystems". It works as a vocabulary even where Backstage is not installed. A subsystem is a System that belongs to a larger System's Domain, or a Component, and a procedure decides which. |
| What kind of page is this | **Diátaxis**: tutorial, how-to guide, reference, explanation | Four types, each with one reader need. Mixing types is the most common structural fault, and a checker can detect it. |
| What does an architecture diagram show at each level | **C4**: context, container, component | One diagram level per hierarchy level, so the diagram on a page is decided by where the page sits. |

Plus two page types Diátaxis does not name, which teams need: **ADR**
(architecture decision record, from Michael Nygard's format) and **runbook**.

## 4. The router: six kinds of task

| Kind | Asked to | Loads, in order |
| --- | --- | --- |
| **Map** | document a team, system, or repo that has no structure yet, or add a new unit | `core/unit-of-documentation.md`, `core/hierarchy.md`, `core/doc-home.md`, `structure/docs-map-template.md`, the nearest `examples/` |
| **Audit** | find what is undocumented, stale, wrong, duplicated, or orphaned | `inventory/README.md`, then `checks/`, then `core/gap-priority.md` |
| **Write** | write or rewrite one page | `docs-map.md` in the project, `core/doc-type.md`, `types/<type>.md`, `core/claims-and-sources.md` |
| **Update** | code changed, fix the docs it affects | `core/change-impact.md`, then **Write** for each page it names |
| **Restructure** | move, merge, split, or migrate existing docs into the map | `core/placement.md`, `core/split-or-merge.md`, `tooling/<tool>/structure.md` |
| **Choose** | settle a dilemma | the one procedure the dilemma table names |

Every task that changes a doc ends with the matching checker run and its
output pasted. A task is not done until the checkers pass.

### Dilemma table (draft)

| Dilemma | Procedure |
| --- | --- |
| Is this thing a team, domain, system, component, API or resource | `core/unit-of-documentation.md` |
| Is a subsystem its own system or a component of the parent | `core/unit-of-documentation.md` |
| Which page type: tutorial, how-to, reference, explanation, ADR, runbook | `core/doc-type.md` |
| At which level does this fact live (team, system, component) | `core/placement.md` (lowest common owner) |
| In the code's repository, or in a team hub | `core/doc-home.md` |
| Docstring, code comment, README, or page | `core/in-code-or-page.md` |
| Handwrite the reference, or generate it (OpenAPI, `--help`, typedoc, Sphinx autodoc) | `core/generated-or-written.md` |
| Split this page or merge these pages | `core/split-or-merge.md` |
| Is this surface documented, only mentioned, or intentionally undocumented | `core/coverage-rule.md` |
| Is this claim verified, and how | `core/claims-and-sources.md` |
| Is this page stale | `core/freshness.md` |
| Which gap first | `core/gap-priority.md` |
| Diagram or prose, and which C4 level | `core/diagrams.md` |
| Who is the reader | `core/audience.md` |
| We know what the code does but not why | `core/rationale.md` (always stop and ask, or cite a source) |
| Does this function need a docstring, and what goes in it | `core/docstring-needed.md` (section 10b) |

## 5. The law file: `docs-map.md`

The Map task produces one file in the documentation home, from
`structure/docs-map-template.md`. After it exists, every other task reads it
first and uses its strings verbatim. The checkers read it. A unit, page or
term that is not in it does not exist; a task that needs one stops and asks.

Tables, read by header, as the observability vocabulary is:

- **Units**: id, kind (Group, Domain, System, Component, API, Resource),
  name, parent, owner, repositories, index page, lifecycle.
- **Pages**: path, unit, type, audience, the one question it answers,
  verified against (repository and commit).
- **Terms**: the project glossary, one term per row, with forbidden synonyms.
- **Surfaces not documented on purpose**: surfaces the Audit must not report,
  each with a reason and who decided.
- **Repositories**: name, clone URL, default branch, docs root, tool.

## 6. Invariants (draft)

1. **A claim about code is a path, a symbol, a command, or a captured
   output.** If you cannot point at one, you do not know it. It goes under
   *Unverified claims*, not into the page.
2. **Never write a why you were not given.** Rationale comes from a person,
   an ADR, a commit message, a pull request or an issue, and is cited. A page
   may say "Rationale: not recorded, ask `<owner>`".
3. **One fact, one place.** Every other page links to it. Duplicated facts
   drift.
4. **A fact lives at the lowest unit that owns all of it.** A parent
   summarises each child in one sentence and links; a child never repeats its
   parent.
5. **Every page has one type and one reader.** A tutorial does not carry
   reference tables; a reference does not teach.
6. **Every page belongs to exactly one unit, and every unit has exactly one
   index page.**
7. **Names come from `docs-map.md` verbatim.** No synonyms for a term in the
   Terms table.
8. **Generated beats written.** If a tool can produce the reference, link to
   or embed its output. Never retype it.
9. **An example was run, or it says it was not.** A command block carries its
   captured output, or the marker `not run`.
10. **A page states what it was verified against.** Repository and commit, in
    the Pages table.
11. **Present tense, current facts.** Plans and intentions go in an ADR with a
    status, or a roadmap, never in a reference or how-to.
12. **When unsure where a fact goes, put it in the lowest unit and link to it
    from above.** Moving a fact up later is cheap; untangling duplicates is
    not.
13. **No secrets, tokens, or personal data in any page,** including in example
    output.

## 7. What an answer ends with

```
## Verdicts
## Claims and sources
## Unverified claims
## Names not in the docs map
## Checker
```

*Claims and sources* lists every factual sentence the answer added, each with
its `path:line`, symbol, or command and output. If *Unverified claims* or
*Names not in the docs map* is not `none`, the answer is a stop and ask. It
proposes the missing rows for a person to approve and does not publish those
sentences.

## 8. Proposed layout

```
skills/documentation/
  SKILL.md                      router, invariants, answer shape
  glossary.md                   fixed words: unit, surface, claim, source, page type...
  core/                         one procedure per dilemma, section 4
  structure/
    docs-map-template.md
    team.md                     what a Group's hub contains, fixed index sections
    domain.md
    system.md                   includes the multi-repository system case
    component.md
    monorepo.md                 one repository, many units
    repository.md               README contract for any repository
  types/                        one template per page type, fixed headings in order
    tutorial.md  how-to.md  reference.md  explanation.md
    adr.md  runbook.md  readme.md  index.md  onboarding.md  changelog.md
  inventory/                    finding the surfaces that need documentation
    README.md                   what a surface is, per kind
    scan_surfaces.py            standard library, heuristic, fixtures per ecosystem
  tooling/                      see sections 10a and 10c
    README.md  choosing.md  paradigms.md
    <tool>/overview.md  install-offline.md  config.md
          structure.md  build-check.md  air-gap-pitfalls.md
  checks/
    check_map.py  check_links.py  check_pages.py
    check_claims.py  check_coverage.py  check_freshness.py  check_style.py
    check_docstrings.py
    fixtures/  run_fixtures.sh
  examples/
    multi-repo-aggregator.md    the current setup, section 10c
    library-repo.md             one package, public API, generated reference
    service-with-subsystems.md  a system and its components, C4 context and container
    multi-repo-system.md        one system across three repositories, team hub
    team-hub.md                 a Group with four systems and shared resources
  evals/evals.json
```

## 9. Checkers

Standard library, Python 3.11, same output contract as observability
(`PASS`, `FAIL`, `WARN`, `SKIP`, `INFO`; exit 0 or 1; `--json`).

| Script | Judges |
| --- | --- |
| `check_map.py` | the map is filled, not a template; every unit has an owner and an index page that exists; parents form a tree; every page in the map exists; every markdown file under a docs root is in the map (orphans) |
| `check_links.py` | relative links and anchors resolve; links into another repository resolve when that clone is present, else `SKIP` with the reason |
| `check_pages.py` | the page has its type's headings in order; first paragraph states the question; no placeholders; no type mixing (for example numbered steps in a reference, a parameter table in a tutorial) |
| `check_claims.py` | every backticked path exists; every `symbol` cited with a path is found in that file; every command's script or target exists (`package.json`, `Makefile`, `pyproject.toml`, `justfile`); every environment variable named appears in the code; every command block has output or `not run` |
| `check_coverage.py` | runs `inventory/scan_surfaces.py` and lists surfaces no page mentions and the map does not exempt, grouped by kind and unit |
| `check_freshness.py` | for each page, the files its claims cite that changed since its verified commit (`git log <commit>..HEAD -- <paths>`) |
| `check_style.py` | forbidden synonyms from the Terms table; banned words (`simply`, `just`, `obviously`, `easy`); future tense in reference and how-to; heading depth; sentence length (`WARN`) |

`check_claims.py` is the accuracy check and the most important one. It
cannot prove a sentence true, but it fails every sentence that points at
nothing, which is where weak-model invention lives.

## 10. Surfaces: how "undocumented" becomes mechanical

A **surface** is anything a reader can touch without reading the code:

| Kind | Found in |
| --- | --- |
| entry point, CLI command and flag | `pyproject.toml` scripts, `package.json` bin, `argparse`/`click`/`typer`/`commander` calls |
| HTTP route | framework decorators and routers, OpenAPI files |
| environment variable | `os.environ`, `os.getenv`, `process.env`, `Bun.env` |
| configuration key | config schemas, settings classes, sample config files |
| public module and export | `__all__`, `index.ts` exports, package `exports` |
| script and task | `package.json` scripts, `Makefile`, `justfile` |
| deployable and its dependencies | Dockerfile, compose, Kubernetes, Helm |
| message topic, queue, event | producer and consumer calls |
| data store and migration | migration folders, ORM models |
| CI workflow | `.github/workflows` |

The scanner is regex over files, per ecosystem, and says so. It over-reports
rather than under-reports, and the map's exemption table absorbs the noise
once. Anything subtler than a regex, such as a route built at runtime, a
type inferred across a virtual environment, or a call path, is not in this
skill. It belongs to the navigation skill (section 13).

## 10a. Tooling knowledge: `tooling/`

The equivalent of observability's `backends/`. The model cannot look up a
tool, so the skill holds what it needs, verified and version stamped.

### Structure

- `tooling/README.md`: a selector, and a filled block for *this
  installation*: which tool is in use for each problem, and its version.
- `tooling/choosing.md`: facts about a situation in, one tool per problem
  out, with the price of each choice. Same shape as
  `backends/choosing.md`.
- `tooling/paradigms.md`: one question per row, one answer per tool. How
  navigation is defined, how versions are published, how search works
  offline, how diagrams render, how API reference is pulled in.
- One folder per tool, same file names in each: `overview.md` (what it
  solves, version, how to read the running version), `install-offline.md`
  (the wheel, npm or container artefacts to mirror, and the command to
  install from the mirror), `config.md` (a complete working config, copied
  whole), `structure.md` (how the docs map becomes navigation),
  `build-check.md` (the strict build command and what each failure means),
  `air-gap-pitfalls.md` (what calls the network by default and how to turn
  it off).

### The problems, and the candidates to research and document

| Problem | Candidates |
| --- | --- |
| Docs site generator | MkDocs with Material, Zensical, Docusaurus, Sphinx, Antora, Hugo |
| Catalog and portal for a team with many systems | Backstage with TechDocs, or a hub repository and a static site |
| API reference from code | mkdocstrings, Sphinx autodoc, pdoc, TypeDoc |
| HTTP API reference | OpenAPI rendered by Redoc or Swagger UI, bundled locally |
| Diagrams | Mermaid, PlantUML, Structurizr for C4, D2, Kroki as a local server |
| Prose and style linting | Vale with a local style package, markdownlint |
| Link checking | lychee in offline mode, the generator's own strict mode |
| Search with no network | the generator's built in index, Pagefind |
| Versioned docs | mike for MkDocs, Docusaurus versioning, Antora branches |
| Decision records | adr-tools, Log4brains, or plain Markdown by template |
| Serving | static files behind nginx or any file server |

### Research rules for writing these files

- Every config key, command and flag is copied from the tool's own
  documentation or source for a pinned version, and the file says which.
- Every recommended config is built once, offline, in a container with the
  network disabled, and the build log is kept in the fixtures.
- Tool status is part of the knowledge. For example, the MkDocs ecosystem is
  in transition (Material for MkDocs moving to maintenance, Zensical as its
  successor); `choosing.md` must state the verified status on the date it was
  written, and the model must not assume a newer state.

### Default recommendation, to be confirmed by the research and by D3

One static site generator for the whole organisation, a hub repository per
team that aggregates per-repository docs folders, generated reference pulled
in rather than written, Mermaid for diagrams because it renders from text in
the page, Vale and lychee in the checks. `choosing.md` decides the generator
from facts: languages in use, whether Backstage already runs, how many
repositories, whether versioned docs are needed.

## 10b. In-code documentation: when a docstring earns its place

Too many docstrings is a defect as real as too few. A docstring that restates
the name and signature costs reading time and drifts. A missing one on a
function with a hidden contract costs a bug. The skill decides from facts,
not taste, in `core/docstring-needed.md`.

**Questions, answered from the code:**

1. Is it public: exported, in `__all__`, in a package's `exports`, called
   from another module or another repository?
2. Do the name, the parameter names and the types together state everything
   a caller must know?
3. Does it do anything the signature hides: raise, mutate an argument, write
   to disk, network, or a global, block, retry, cache, or depend on call
   order?
4. Does a value carry a unit, a range, a format, or a sentinel meaning
   (seconds or milliseconds, `None` means "all", `-1` means "unlimited")?
5. Does it return an untyped shape (`dict`, `Any`, a tuple) whose keys or
   positions a caller must know?
6. Is there a non-obvious reason it is written this way, recorded in a
   commit, a pull request or an issue?

**Verdict:**

- No to 1, yes to 2, no to 3 to 6: **no docstring**. An existing one that
  restates the name is deleted.
- Yes to 3, 4, 5 or 6: **a docstring naming exactly those facts**, one line
  each, and nothing else. No retelling of the body.
- Yes to 1 and no to 2: **a one-line summary**, plus 3 to 6 as they apply.
- 6 without a source: a comment is not written; stop and ask (invariant 2).

**Never:** a docstring that repeats parameter names and types already in the
signature; a comment that says what the next line does; a docstring on a
private helper whose name says it all.

**Checker:** `check_docstrings.py`, Python through the standard library `ast`
module, TypeScript and JavaScript by pattern. It reports **restating**
docstrings (every content word is already in the function or parameter
names), and **missing** ones on public functions that raise, touch I/O,
return an untyped shape, or take a parameter named like a unit
(`timeout`, `delay`, `size`, `limit`). Both are `WARN` with the question
number that decides it, because the final call is the procedure's, not the
pattern's.

## 10c. The case this skill must handle first: your current setup

Each repository keeps its own docs folder. A downstream repository pulls them
together and builds one site, with MkDocs or Read the Docs. That is a real
pattern, the multi-repository aggregator, and it becomes the first worked
example and the first eval, built from the real repositories.

What the skill must be able to do with it:

- **Audit it as it is**: which repositories feed the aggregator, how
  (git submodules, a copy step in CI, a plugin such as a multirepo or
  monorepo plugin), which pages fall out of the navigation, which links
  break across repositories, which pages are stale.
- **Decide whether to keep it**, through `tooling/choosing.md`: keep the
  aggregator and fix it, move to Backstage with TechDocs (each repository
  publishes its own docs, the catalog provides the team, system and
  component hierarchy), or another generator.
- **Migrate it**, as a Restructure task, if the verdict says move.

Read the Docs is a hosting and build service, not a generator. It builds
Sphinx or MkDocs. Its hosted service needs the internet, and self-hosting it
is heavy, so in an air-gapped setting it is usually the wrong layer to depend
on. The research will confirm this and state it in `tooling/choosing.md`.

Backstage fits the hierarchy problem directly, since its catalog already has
teams, systems and components, but it is a service to run, upgrade and
mirror offline. The choosing procedure weighs that against keeping a static
aggregator. No verdict until the aggregator repository has been read.

## 11. Worked examples

Five examples, as in section 8. Each holds a small fictional codebase, its
`docs-map.md`, its pages, and the checker output. `extract_golden.py` pulls
them out and `run_fixtures.sh` runs every checker on them, so the examples
cannot drift from the rules. Same mechanism as observability.

## 12. Evals (written before the procedures)

Draft scenarios, each baiting one known failure:

| # | Prompt, short | Bait | Expected |
| --- | --- | --- | --- |
| 0 | "Document this repo" (no docs at all) | writes a long README first | runs Map: units, page list, owners asked for; no prose yet |
| 1 | "Write the README, I think it retries three times" | repeats the user's guess | cites the retry code or lists the claim as unverified |
| 2 | "Explain why we use Redis here" (no ADR, no commit history on it) | invents a rationale | stops and asks; offers an ADR stub with rationale `not recorded` |
| 3 | A system across three repositories, each repository's README describes the system differently | picks one and copies it | system page in the team hub, repositories link up, conflicting facts listed as stop and ask |
| 4 | A fact about auth is in the system page and in two component pages | edits all three | moves it to the lowest owner, replaces the others with links |
| 5 | A tutorial with a forty-row configuration table in it | polishes the tutorial | splits into tutorial and reference, links them |
| 6 | "What is undocumented here" | reads files and guesses | runs the scanner and coverage checker, ranks gaps by `core/gap-priority.md` |
| 7 | A pull request diff, "update the docs" | updates only the README | runs `check_freshness.py`, lists every affected page |
| 8 | An OpenAPI file exists, "document the endpoints" | handwrites an endpoint table | links or embeds the generated reference |
| 9 | "Just write something quick about the config, you can guess the defaults" | guesses defaults | reads them from code or stops and asks |
| 10 | A team with five systems, "organise our docs" | invents a folder scheme | maps to Group, Domain, System, Component via the procedure, produces the map |
| 11 | A monorepo with twelve packages | one README for everything | one unit per package that passes the unit procedure, one monorepo index |
| 12 | "Add docstrings to this module" (half its functions are self-explanatory) | docstrings everywhere | applies `core/docstring-needed.md` per function; some get none, restating ones are removed |
| 13 | A function takes `timeout` with no unit and returns a `dict` | "Returns a dict." | a docstring naming the unit and the keys, sourced from the code |
| 14 | "Our aggregator site is missing pages and links are broken" | edits the site config by guess | audits which repositories feed it and how, runs the link and map checkers, lists the causes |

Run each on MiniMax 2.7 if we have access (decision D5), otherwise on a small
stand-in, with only the skill folder readable. Record runs in `evals.json` as
observability does, fix what fails, rerun.

## 13. The skill family, and where documentation sits in it

I agree that navigation is a must. The documentation skill's central rule is
that every claim points at a path, a symbol or a command. A weak model can
only keep that rule if it can reliably find those things, across
repositories, through virtual environments and inferred types. Without a
navigation skill, most explanation pages end in "stop and ask", and the
skill is much less useful.

Proposed family, in three layers:

1. **Seniority: sharper reasoning, for any task.** It knows no other skill
   by name. It teaches scoping, choosing tools by reading their
   descriptions, telling evidence from memory, challenging ideas, breaking
   loops, and checking before saying done. Its own plan is
   `plans/seniority-skill.md`.
2. **Capability skills.** Used by every domain skill.
   - **Navigation**: find the entry points, follow a call path, resolve what
     a name refers to, read inferred types, locate and activate the right
     environment, read runtime wiring (config, dependency injection). Its
     tools are backends, the way Elastic and Grafana are for observability:
     ripgrep, universal-ctags, a language server, and **Sourcegraph** for
     cross-repository search. Same questions, a folder per tool, a choosing
     procedure for which one is available.
   - **Execution**: install dependencies from an offline mirror, run a
     command, capture output. Needed so examples are run, not guessed.
   - **Git archaeology**: blame, the commit and pull request behind a line,
     what changed since a commit. Feeds rationale and freshness.
3. **Domain skills.** Observability, documentation, and later others.
   Diagramming (C4, Mermaid) and writing style stay inside documentation
   until a second skill needs them.

No skill routes to another by name. A skill names the **question** it needs
answered; the model finds a skill whose description answers it, as
seniority's tool choosing procedure teaches. The authoring rules shared by
all skills (procedure shape, law files, answer headings, checker contract,
eval format) live in `CANON.md` at the repository root, for authors.

**The contract between them.** Each capability skill answers a fixed set of
questions in a fixed shape, so a domain skill can rely on it:

| Question from documentation | Typically answered by | Answer shape |
| --- | --- | --- |
| Where is this surface implemented | a navigation capability | `path:line`, symbol |
| Who calls this, what does it call | a navigation capability | list of `path:line` |
| Is this claim true | a navigation capability | yes or no, with `path:line` |
| What does this command print | an execution capability | the command, its exit code, its output |
| Why is it like this | a git history capability | commit, pull request, or `not recorded` |
| Has this changed since commit X | a git history capability | list of changed paths |

The answer shapes are fixed in `CANON.md`. Documentation asks the question;
if no available skill answers it, the answer is "stop and ask", naming the
missing capability.

## 14. Build order

1. Decisions in section 15.
2. `CANON.md`, extracted from the observability skill.
3. Seniority, per `plans/seniority-skill.md`.
4. Navigation, with ripgrep and ctags first, Sourcegraph once D2 is answered.
   Execution and git archaeology as folders of navigation at first.
5. Documentation: evals first, from the real aggregator setup; then router,
   invariants, procedures, templates, scanner, checkers, examples, tooling.
6. Weak-model eval runs across the family, then a consistency pass against
   the canon.

## 15. Decisions needed from you

### D1. The skill family

Seniority as a reasoning skill that knows no other skill; navigation,
execution and git archaeology as capability skills; documentation and
observability as domain skills; `CANON.md` for authors. *Recommended:* yes,
with execution and git archaeology as folders inside navigation at first.
Seniority's own decisions are in `plans/seniority-skill.md`.

### D2. Sourcegraph

Do you run a self-hosted Sourcegraph inside the air-gapped network, and is
there already a skill for it? If yes, navigation treats it as its main
backend for cross-repository questions.

### D3. The aggregator repository

Which repository builds the combined site today? Once I can read it, I can
confirm MkDocs or Read the Docs, and the keep, fix or move to Backstage
decision becomes a verdict from facts rather than a guess.

### D4. Which languages the scanner and the docstring checker cover

*Recommended:* Python and TypeScript/JavaScript first. Others?

### D5. The eval model

Can we run MiniMax 2.7 for evals, and through what? A smarter stand-in hides
failures.

### D6. May the skill edit code

With section 10b in place, it can delete restating docstrings and add
missing ones. Should it change code directly, or propose the changes?
