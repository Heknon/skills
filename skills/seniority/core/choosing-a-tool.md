# Choosing a tool

**Verdict you produce:** the tool or skill for this step, and why, in one
line: `verdict choosing-a-tool: <tool> because it answers <question> with <shape>`.

You do not know in advance which tools and skills this environment has.
You find out by reading what is available and matching it to the question.
This file teaches the matching. It names no skill, because the right one
is whichever one here says it answers your question.

## Questions

1. **What question must this step answer, and what shape is the answer?**
   Write it as a question. The shapes:
   - a **location**: a file and line, a symbol;
   - a **yes or no**;
   - a **value**: a version, a setting, a count, a duration;
   - a **list**: callers, files, errors;
   - a **reason**: why something is the way it is;
   - a **decision** only a person can make.
2. **Which available tools or skills say they answer this?** Read their
   names and descriptions. Match on the nouns of your question and on its
   domain. A skill whose description names the domain of your question,
   such as traces, documentation, a query language, a code search service,
   carries procedures and facts that general reasoning does not: load it
   before answering from your own knowledge.
3. **Of those, which is the narrowest?** Walk the ladder below from the
   top, and take the first rung that can answer.
4. **Does it give evidence you can quote, or only an opinion?** Prefer the
   one whose output you can copy into your notes.
5. **Does it change anything?** For a question about the current state,
   use a tool that only reads.

## The ladder

| Rung | Tool | Answers |
| --- | --- | --- |
| 1 | a search for a name or a phrase | locations, lists of uses |
| 2 | a file listing, a directory tree | what exists, where |
| 3 | reading the part of a file a search pointed at | a value, a definition |
| 4 | a program's own help, version or dry-run output | flags, versions, what it would do |
| 5 | running the program or the test | yes or no, a value, an error |
| 6 | history: the log of changes, who changed a line and why | a reason |
| 7 | a skill for the domain | a procedure and its verdict |
| 8 | a person | a decision, an intent, access you lack |

A skill (rung 7) is not more expensive than running a program; it sits
there because it is only useful once you know the question's domain. When
the domain is known at Start, load its skill at Start.

## Common questions and their first tool

| Question | First tool | Not |
| --- | --- | --- |
| where is X defined | search for its definition: `def X`, `class X`, `function X`, `X =` | reading files in order |
| who uses X | search for `X` across the code, then across configs and scripts | assuming nothing does |
| what flags does this command take | its `--help` | memory |
| which version is installed | its version command | the version in a lock file, which may not be what is installed |
| does this work | run it | reading it and deciding |
| why was it written this way | the history of that line, then its commit message | inventing a reason |
| what does the person want | ask | guessing twice |

## Never

- Never answer from memory a question one tool call could answer.
- Never load a skill whose description does not match your question "just
  in case". It costs context and adds rules that do not apply.
- Never use a tool that changes state to find out what the state is.
- Never pick a tool because it is the one you used last.

## Stop and ask

- No available tool can answer, the fact matters for the goal, and a person
  might know. Ask for the fact, not for permission to guess.
