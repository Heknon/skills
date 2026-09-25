# Writing

**What it decides:** how a page reads, sentence by sentence.

1. **The first sentence says what the page is for**: what it answers or
   what the reader can do after it.
2. **Short sentences.** One idea each. A sentence with two "and"s is two
   sentences.
3. **Exact names in code format**: `charge()`, `--dry-run`,
   `BILLING_TIMEOUT`, `src/billing/charges.py`.
4. **Present tense, active voice**: "`charge()` retries three times", not
   "will be retried".
5. **Steps are numbered and start with a verb**: "Run", "Open", "Set".
   One action per step. Show the command, then what it prints.
6. **Say it once and link.** If another page already states it, link to
   that page instead of restating it.
7. **Match the docs around it.** Before writing, read two pages next to
   where yours will go. Copy their heading style, their tone, how they
   show commands and paths, and their front matter if any.
8. **Cut:** "simply", "just", "easy", "obviously", "note that", "it should
   be noted", "in order to", and every sentence that restates the heading.
9. **Links** are relative paths to `.md` files, so the site's strict build
   can check them: `[charges](../billing/charges.md)`.
10. **Commands** are PowerShell for this team, and Python runs through
    `uv run`.
