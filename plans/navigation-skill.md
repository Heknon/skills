# Plan: the navigation skill

Status: draft for decision. Nothing is built yet.

## 1. What it is

The capability every engineering task depends on: finding your way in code
you have never seen. Where something is defined, who calls it, what it
calls, how data gets from one place to another, which file a name really
refers to, what type a value has, how the program starts, and which
environment it runs in. It answers with locations (`path:line`) and
evidence, never with a guess.

It follows what the seniority evals taught: a skill carries knowledge and
judgement, not enforcement. No files to write, no scripts the model must
remember to run.

## 2. The environment it is written for

- **Zed's agent, air gapped, a weak model.** The tools are `grep`
  (regular expressions over file contents), `find_path` (glob), `read_file`,
  `list_directory`, `diagnostics` (the language server's errors and
  warnings), and `terminal`. There is no go-to-definition, no
  find-references, no hover type. The skill turns each of those into a
  search, a read or a terminal command that works.
- **No web.** Everything the model needs about a language's import rules,
  a tool's flags, or a framework's wiring is written into the skill.
- **Whatever is installed.** The skill never assumes ripgrep, ctags, a
  type checker or Sourcegraph exists; it checks first, and has a path
  that needs only the built-in tools.

## 3. The questions it answers

The router is a list of questions, each with the answer's shape.

| Question | Answer shape |
| --- | --- |
| **Orient**: what is this repository, how is it laid out, how does it start, build and test | entry points, commands, the map of top folders, each with the file that proves it |
| **Locate**: where is `X` defined | `path:line`, and how the name was resolved |
| **Trace in**: who calls or uses `X` | a list of `path:line`, with what the search could not see (dynamic calls, other repositories) |
| **Trace out**: what does `X` call, read, write | a list of `path:line` |
| **Follow**: how does a value or request get from A to B | a chain of `path:line` hops |
| **Resolve**: what does this name, import or type actually refer to | the file and definition, and the rule that resolved it |
| **Environment**: which interpreter, runtime and packages run this, and how to run it | the commands that show it, and their output |
| **History**: when and why did this change | commit, author, message, or `not recorded` |

## 4. Layout

```
skills/navigation/
  SKILL.md                 router over the eight questions, invariants, answer shape
  glossary.md
  core/                    language-neutral procedures, one per question
    orient.md  locate.md  trace-in.md  trace-out.md  follow.md
    resolve.md  environment.md  history.md
    search-patterns.md     how to write a grep that finds definitions, not mentions
    what-search-misses.md  dynamic dispatch, string lookups, registries, generated code
  languages/               same file names in each folder
    python/
      definitions.md       def, class, assignment, decorators, __all__
      imports.md           module resolution, packages, relative imports, sys.path, namespace packages
      entry-points.md      __main__, console scripts, frameworks' routing
      environment.md       venv, uv, poetry, conda, pip; which interpreter runs
      types.md             reading annotations, stubs, reveal_type, running a checker offline
      dynamic.md           getattr, importlib, entry points, dependency injection, registries
    typescript/            the same files for TypeScript and JavaScript on Node and Bun
  tools/
    grep.md                the built-in grep, ripgrep if present, patterns that work
    terminal-probes.md     asking the running interpreter: where a module lives, its source, a value's type
    git.md                 log, blame, pickaxe, log of a line range
    type-checkers.md       pyright, mypy, tsc: offline use, what each output means
    sourcegraph.md         cross-repository search, when an instance exists
  examples/                worked navigations with the real searches and results
  evals/evals.json         sandboxes that bait each failure
```

## 5. The failures it targets

| Failure | What it looks like |
| --- | --- |
| **Mention for definition** | grep finds the name in a comment or a call and reports it as the definition |
| **Wrong file of the same name** | two `config.py` or `utils.ts`; the model reads the wrong one |
| **Missed indirection** | the name is re-exported, aliased, or imported under another name, and the trail stops |
| **Invisible callers** | calls through `getattr`, a registry, a decorator, a route table or a string, which grep for the name never finds; the model says "nothing calls it" |
| **Wrong environment** | reads the source in the repository but a different installed version runs |
| **Reading everything** | opens files in order instead of searching |
| **Invented types** | states a type from the name of a variable |

## 6. Evals, written first

Sandboxes in Python and TypeScript, each baiting one failure above: a
name defined twice in different packages, a function only ever called
through a registry, a re-export chain three deep, a TypeScript path alias,
a repository whose installed package differs from its source, a route
registered by decorator, and an orientation task on an unfamiliar layout.

## 7. Decisions needed

### N1. Languages

*Recommended:* Python and TypeScript/JavaScript first, since that is what
`morphine-sahara-mock-api` uses. Others?

### N2. What is installed in the air-gapped environment

Ripgrep, universal-ctags, pyright or mypy, tsc? The skill works without
them, but each one it can count on makes an answer more exact.

### N3. Sourcegraph

Is there a self-hosted Sourcegraph inside the network? If yes, it becomes
the tool for questions that cross repositories. If no, the skill says how
to search several local clones instead.

### N4. Git history

*Recommended:* inside navigation, as the History question, not a skill of
its own.
