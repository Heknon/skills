# Claims

**What it decides:** whether a sentence may go into a page, and how to
back it.

A documentation page is a list of claims about the code. A wrong claim is
worse than a missing one, because readers act on it. Weak writing states
what code like this usually does; good writing states what this code
does, and shows where.

## Kinds of claim and how to back each

| Claim | Backed by | Use |
| --- | --- | --- |
| "X exists", "X is in module Y" | the definition, `path:line` | navigation, Locate |
| a default value, a limit, a timeout, a retry count | the line that sets it | navigation, Locate; read the line |
| "X calls Y", "X is used by Z" | the call sites | navigation, Trace out or Trace in |
| what a function returns or raises | its annotations, docstring, or a type checker | navigation, Resolve and types |
| an option, a flag, an environment variable | the code that reads it, or the program's `--help` | navigation search for `os.environ`, `getenv`, `add_argument`, settings classes |
| a command works and prints this | running it | `uv run ...`, output copied |
| how to install or run | the project files and CI | navigation, Orient |
| why it is this way | a commit, pull request, issue, ADR, or a person | navigation, History; never inference |
| who owns it | a CODEOWNERS file, the team page, or a person | read or ask |

## Rules

1. **Read the line before you write the sentence.** Not the name of the
   function, not the neighbouring comment: the line that does it.
2. **Copy exact names.** Function, option, variable and file names are
   copied from the code, with their case.
3. **Numbers come from code or output.** Never round, never "about".
4. **The person asking is a source for intent, not for behaviour.** "I
   think it retries three times" is a hypothesis. Check the code; if it
   says five, the page says five, and you tell the person.
5. **Existing docs are not a source.** They may be stale. Confirm each
   claim you keep against the code.
6. **When you cannot confirm a claim**, do not write it as fact. Leave it
   out, or write it with a visible marker, `> Not verified: <what would
   confirm it>`, and list it under *Not verified*.

## Where the source goes

In your answer, under *Sources*, one line per claim you added. Not in the
page: readers need the fact, not your search. A page names a file only
when the reader needs it, such as where settings are read.

## Never

- Never write a claim because it would be typical for this kind of code.
- Never write a reason (a "because", "so that", "to avoid") that no
  record gives.
