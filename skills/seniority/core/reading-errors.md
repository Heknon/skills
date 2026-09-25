# Reading errors

**Verdict you produce:** the error that matters, copied exactly, where it
was raised, its category, and the first check for that category:

```
verdict reading-errors: <exact message> at <path:line> | category: <category> | first check: <action>
```

You cannot search the web for an error message here. Everything you need
is in the output in front of you and in the code. Most errors say exactly
what is wrong; the mistake is reading the wrong one, or reading it loosely.

## Questions

1. **Which error came first?** Scroll up. Later errors are often caused by
   the first one: a failed import makes every later name undefined. The
   first one is the one to read.
2. **What is the exact message?** Copy it into your notes, character for
   character. Do not paraphrase it.
3. **Where was it raised?** In a traceback, find the deepest frame that is
   in this project's code, not in a library. That line is where your code
   met the problem. The library frames below it say how.
4. **Which category is it?** Use the table.
5. **What changed since it last worked?** A dependency, a config, the
   environment, the input, the code. If nothing you know of changed, the
   input or the environment did.
6. **Is it about the input or about the code?** A validation error names
   the input. A type error or a missing attribute names the code.

## Categories and the first check

| Category | Looks like | First check |
| --- | --- | --- |
| **not installed** | `ModuleNotFoundError`, `Cannot find module`, `command not found` | which interpreter or runtime is running, and whether the package is installed in that one, not in another |
| **not found** | `FileNotFoundError`, `ENOENT`, `No such file` | the current directory and the absolute path the program built |
| **not defined** | `NameError`, `KeyError`, `undefined`, `AttributeError` | print what does exist: the keys, the attributes, the names in scope |
| **wrong type or value** | `TypeError`, `ValueError`, a validation error | print the actual value and its type at the line raised |
| **cannot connect** | `Connection refused`, `timed out`, `Name or service not known` | is the service running, on that host and port; air-gapped, is the program trying to reach the internet |
| **not allowed** | `Permission denied`, `EACCES`, `403`, `401` | which user runs it, the file's mode, which credential is sent |
| **parse** | `SyntaxError`, `unexpected token`, `invalid YAML` | the line and column named, and the line before it, where the cause usually is |
| **expectation** | a test assertion, `expected X got Y` | compare the two values literally; then ask whether the test or the code is right |
| **resource** | `MemoryError`, `No space left`, `Killed`, exit 137 | measure memory or disk at the moment of failure |
| **version** | `unsupported`, `deprecated`, an API that "does not exist" | print the installed version and compare with what the code expects |

## Warnings

Read the warnings before the error. After an upgrade, a deprecation
warning is often the cause, printed long before the failure.

## Never

- Never fix the last error in a cascade before the first.
- Never paraphrase an error in your notes. Copy it.
- Never retry the same command hoping the error goes away. That is the
  first half of a loop.
- Never silence an error to make the output clean, by catching and
  ignoring it, or by skipping the check that raised it.

## Stop and ask

- The first error is not in the output you have: it is in a log you cannot
  read. Say which log, and where it usually lives.
