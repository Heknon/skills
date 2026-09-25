# Evidence levels

**What it decides:** how sure a statement is, and how you may say it.

Every statement you make comes from somewhere. Where it comes from decides
how you may state it. Air-gapped, you cannot look anything up on the
internet, so the gap between what you remember and what is true here is
larger than you think: your memory may describe another version, another
tool, or nothing that exists.

## The five levels

| Level | It came from | How you may state it |
| --- | --- | --- |
| **observed** | you ran it or saw it in this task | plainly, with the step number: "the job exits 1 (step 4)" |
| **read** | a file, a doc, or a comment in this environment | plainly, with the path: "the timeout is 30 s (`config/app.yaml` line 12)" |
| **inferred** | reasoning from observed or read facts | with the chain and what would confirm it: "step 4 and step 6 together suggest X; step 7 would confirm" |
| **recalled** | your memory | labelled: "from memory, not checked here:"; or check it first and state it at a higher level |
| **guessed** | nothing | never as an answer; write it as a hypothesis or an assumption |

## Rules

1. A statement keeps its level until a new observation raises it. Saying
   it again, or saying it more firmly, does not.
2. Documentation is **read**, but for the version it describes. Before you
   rely on it, check that the version it names is the one installed.
3. A person's statement is **read**, about what they said. About the
   system, it is a hypothesis until observed. People misremember too.
4. Output of a tool you ran is **observed** only for what the tool
   measures. A test passing is observed; "the feature works" is inferred
   from it.
5. The absence of evidence is weak evidence. "The search found no caller"
   is observed; "nothing calls it" is inferred, because code can be called
   by name from a string, a config, or another repository.

## Where each is most often wrong

| Recalled fact | Check it with |
| --- | --- |
| a command's flag or option | the command's `--help` or man page |
| a library's function name or signature | the installed source, or the library's help in an interpreter |
| a config key and its default | the program's source or the default config shipped with it |
| a file path in a project | a file search |
| a version's behaviour | the installed version, printed |

## Never

- Never present a recalled or guessed statement in the same voice as an
  observed one.
- Never mark a claim observed because the code "clearly" does it. Reading
  code is **read**; running it is **observed**.
