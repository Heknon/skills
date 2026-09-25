# Page types

**What it decides:** which kind of page to write, and so which template
to use and what to leave out.

Every page has one reader with one need. Mixing needs makes a page that
serves none of them: a tutorial full of reference tables loses the
learner; a reference that stops to teach buries the facts. The four main
kinds are the Diátaxis framework's; two more are common in teams.

| Kind | The reader is | They want | Template |
| --- | --- | --- | --- |
| **tutorial** | new, learning | to get something working once, guided, start to finish | `templates/tutorial.md` |
| **how-to** | working, has a goal | the steps for one task, nothing else | `templates/how-to.md` |
| **reference** | working, looking something up | complete, exact facts in a fixed order | `templates/reference.md` |
| **explanation** | trying to understand | how and why it works, the design, the trade-offs | `templates/explanation.md` |
| **decision record (ADR)** | anyone, later | what was decided, why, what else was considered | `templates/adr.md` |
| **runbook** | on call, under pressure | what to check and do when something is wrong | `templates/runbook.md` |

A repository's `README.md` and each unit's index page are their own kind:
`templates/readme.md` and `templates/index.md`.

## Deciding

Ask what the reader will do with the page:

1. Follow it once to learn: **tutorial**.
2. Follow it to finish a real task they already understand: **how-to**.
3. Look something up and leave: **reference**.
4. Read it to understand: **explanation**.
5. Learn why a choice was made: **ADR**.
6. Act during an incident: **runbook**.

## Split a mixed page

Signs of mixing: numbered steps inside a reference; a table of every
option inside a tutorial or how-to; long "why" paragraphs inside steps;
steps inside an explanation. Split by moving each part to a page of its
kind and linking between them. Keep the original path for the kind most
readers came for, so existing links keep working.

## Never

- Never add a reference table to a tutorial or how-to "for completeness".
  Link to the reference.
- Never write a reference by hand when it can be generated: API reference
  from docstrings (`mkdocs/api-reference.md`), command options from
  `--help`.
