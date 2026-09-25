---
name: documentation
description: Write, fix and organise documentation for Python code and the teams and systems around it, published with MkDocs or Zensical, air gapped. Write a page of the right kind, add or remove docstrings where they earn their place, find what is undocumented, stale, wrong or duplicated, decide where a fact belongs across a team, its systems, subsystems and repositories, update docs after a code change, and run the docs site, including combining several repositories into one site, offline diagrams, API reference, and moving from MkDocs to Zensical or planning a move to Read the Docs. Every claim in a page points at the code, command or record that shows it.
---

# Documentation

This skill writes documentation that is true, in the right place, of the
right kind, and no longer than it needs to be. It knows how to structure
docs for one repository, a system of several, and a team of several
systems, and how to run the MkDocs or Zensical site that publishes them.

It relies on the **navigation** skill for every fact about the code:
where something is defined, who calls it, what it returns, what changed.
Load it too. A documentation claim is only as good as the location that
backs it.

## The six tasks

| Task | Asked to | Load |
| --- | --- | --- |
| **Write** | write or rewrite a page, a README, a how-to, a reference | `core/page-types.md`, the template in `templates/`, `core/claims.md`, `core/writing.md` |
| **Docstrings** | document functions and classes in the code, or clean up their docstrings | `python/docstrings.md` |
| **Audit** | find what is undocumented, stale, wrong or duplicated | `core/find-gaps.md` |
| **Structure** | organise docs for a repository, a system, a team; decide where something goes | `core/structure.md` |
| **Update** | code changed; fix the docs it affects | `core/update-after-change.md` |
| **Site** | build, fix, extend or migrate the MkDocs or Zensical site; plan a move to Zensical or Read the Docs | `mkdocs/status.md` first, then the file it names |

A task often needs two: an Audit before a Write, a Structure before
several Writes.

What counts as a surface to document is in `python/surfaces.md`. Page
templates are in `templates/`. `examples/` holds three worked tasks: a
docstring clean-up (`docstrings.md`), a guess in the ask
(`a-guess-in-the-ask.md`), and a page missing from the combined site
(`missing-pages.md`). `glossary.md` fixes the words.

Nobody may be there to answer. Never stop a task to ask about one claim:
leave it out or mark it, list it under *Not verified*, and go on.

## The check before you save any page or docstring

Read every sentence you wrote. For each number, default, name, unit,
command output and reason in it, name the line, the output you saw, or
the record it came from. **If you cannot, delete it or mark it not
verified.** Most of all:

- **A value the person gave you.** Check it in the code. If the code
  differs, write the code's value and tell them. "Use my number" or "you
  can guess" does not change this.
- **A unit the code does not state.** A `timeout` passed on to another
  library is not "seconds" until that library's code says so.
- **Output you did not see.** Show output only from a command you ran;
  otherwise the block says `not run`.
- **A reason.** Any "because", "to reduce", "so that", "the trade-off is
  made to" needs a record. Without one, delete the sentence, in the
  introduction and under *Trade-offs* too; do not write a reason next to
  `Reason: not recorded`.

*Not verified: none* is a claim too: only write it after this check.

## Invariants

1. **Every factual sentence points at its source.** A path and line, a
   command and its output, a commit, or a person. What navigation cannot
   confirm is marked unverified or left out (`core/claims.md`).
2. **Never write a reason you were not given.** Why something is built a
   certain way comes from a commit, a pull request, an issue, an ADR or a
   person. If none says, leave the reason out; where a page needs one (an
   explanation, an ADR), write `Reason: not recorded`.
3. **One fact, one place.** Everywhere else links to it. A fact written
   twice drifts.
4. **A fact lives at the lowest level that owns all of it**: a function's
   contract in its docstring, a component's setup in its repository, a
   system's shape on the system page, the team's conventions on the team
   page. A parent summarises its children in one line each and links
   down; a child never repeats its parent.
5. **One page, one kind, one reader.** A tutorial teaches, a how-to
   solves one task, a reference lists, an explanation explains
   (`core/page-types.md`). Mixed pages are split.
6. **Generated beats written.** API reference comes from the docstrings
   through mkdocstrings; command options from the program's `--help`.
   Never retype what a tool produces.
7. **An example was run, or it says it was not.** A command block shows
   the output it really gave, or is marked `not run`.
8. **Present tense, current facts.** Plans go in an ADR or a roadmap, not
   in a reference or how-to.
9. **Editing code for docs changes nothing else.** A docstring or comment
   edit never changes behaviour, and is checked by importing the module
   and running the tests.
10. **The site builds offline and strict.** No page, font or script comes
    from the internet, and `--strict` passes (`mkdocs/site.md`).

## What you say when you finish

```
## Changed
<each file changed, one line each, with what changed>

## Sources
<each factual claim you added, and where it comes from: path:line, command, commit, person>

## Not verified
<claims you could not confirm, and what would confirm them, or none>

## Not done
<gaps you found and left, pages that should change but were not asked for, or none>
```

If another skill is loaded, its closing headings come after these.

The `evals/` folder is for people testing this skill. Never open it while
doing a task.
