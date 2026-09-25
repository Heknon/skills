---
name: navigation
description: Find your way in Python code you have never seen, on Windows, without go-to-definition. Where a name is defined, who calls or uses it, what it calls, how a value or request travels from one place to another, what an import or name really resolves to, what type a value has, how the program starts, builds and tests, which interpreter and packages actually run it, and when and why code changed. Uses search, file reading, the terminal, the ty, mypy and Pyright type checkers, git, and Sourcegraph when it is connected. Answers with file and line, never a guess.
---

# Navigation

This skill finds things in code. It answers with a location, `path:line`,
and the search or command that proves it. It never answers from what a
name suggests or from memory of how such code usually looks.

Your editor gives you search, file reading and a terminal, but no
go-to-definition, no find-references and no hover type. This skill turns
each of those into searches, reads and commands that work. The terminal is
Windows PowerShell; commands here are written for it.

## The eight questions

Decide which one you are answering, then load its file and nothing else.
A task often needs several in turn, such as Orient, then Locate, then
Trace in.

| Question | You were asked | Answer shape | Load |
| --- | --- | --- | --- |
| **Orient** | what is this repository, how does it start, build, test | entry points and commands, each with the file that shows it | `core/orient.md` |
| **Locate** | where is `X` defined | `path:line`, and how the name was resolved | `core/locate.md` |
| **Trace in** | who calls or uses `X`; is it safe to change or delete | every use as `path:line`, and what the search could not see | `core/trace-in.md` |
| **Trace out** | what does `X` call, read or write | every call, read and write as `path:line` | `core/trace-out.md` |
| **Follow** | how does a value or a request get from A to B | a chain of hops, each `path:line` | `core/follow.md` |
| **Resolve** | what does this import, name or type really refer to | the file and definition, and the rule that resolved it | `core/resolve.md` |
| **Environment** | which interpreter and packages run this; how to run it | the commands that show it and their output | `core/environment.md` |
| **History** | when and why did this change | commit, author, date, message, or `not recorded` | `core/history.md` |

Two files apply to every question: `core/search-patterns.md` (how to
search for a definition and not a mention) and `core/what-search-misses.md`
(the uses no search for the name will find). Read both once per task.

Python-specific knowledge is in `python/`. Tool knowledge is in `tools/`.
Load the file a procedure names, when it names it. `examples/` holds three
worked navigations: through re-exports (`locate-through-reexports.md`), a
function only reached through a registry (`is-it-used.md`), and an
installed copy running instead of the source (`old-code-runs.md`).
`glossary.md` fixes the words.

## Tools, cheapest first

1. **The editor's search tools**: `grep` for text by regular expression,
   `find_path` for file names by glob, `list_directory`, `read_file`.
   `tools/zed-tools.md`.
2. **The language server's diagnostics** through `diagnostics`: errors such
   as an unresolved import tell you what the editor itself cannot find.
3. **Sourcegraph**, when its tools are available (`go_to_definition`,
   `find_references`, `keyword_search`, `read_file` with a `repo`): exact
   definitions and references, across every repository it indexes.
   `tools/sourcegraph.md`.
4. **The running interpreter**, through the terminal: where a module
   really lives, its source, a signature, what is installed.
   `tools/terminal-probes.md`.
5. **A type checker**: ty, mypy or Pyright, for what type a value has.
   `tools/type-checkers.md`.
6. **git**, for history. `tools/git.md`.

## Invariants

1. **A location is `path:line` you have read.** A search hit is a lead
   until you open the file at that line and see the definition or use.
2. **A definition is found with a definition pattern.** Searching for the
   bare name finds mentions: comments, strings, calls, other things with
   the same name.
3. **A name is resolved from the file that uses it.** Two definitions with
   the same name are common; the one that counts is the one the using
   file's imports lead to.
4. **"Nothing uses it" is never proved by one search.** Before saying it,
   go through `core/what-search-misses.md`.
5. **What runs is what the interpreter imports, not what the repository
   contains.** When behaviour and source disagree, ask the interpreter
   where the module is (`tools/terminal-probes.md`).
6. **A type is read from annotations or a checker, never from a name.**
   Say which checker, and copy its line.
7. **Search before you read, read the part the search points at.** Do not
   open files in order to look for something.

## What you say when you answer

```
## Found
<one line per location: path:line, and what is there>

## How I know
<each search or command, and what it returned that shows it>

## Not covered
<what the searches could not see, from core/what-search-misses.md, or none>
```

If another skill is loaded, its headings come first and these come after.

The `evals/` folder is for people testing this skill. Never open it while
doing a task.
