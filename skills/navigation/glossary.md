# Glossary

One sentence per term. Use these words and no synonyms.

| Term | Meaning |
| --- | --- |
| location | A file and line, `path:line`, that you have opened and read. |
| hit | A line a search returned; a lead, not yet a location. |
| definition | The line that creates a name: `def`, `class`, or an assignment. |
| mention | Any other line containing the name: a call, an import, a comment, a string. |
| use | A mention that makes the code run or depend on the name: a call, a registration, a subclass, an import that is used. |
| re-export | An import in one module, often an `__init__.py`, that makes a name available from there although it is defined elsewhere. |
| resolve | Follow a name or import from the file that uses it to the definition that file really reaches. |
| search path | `sys.path`: the folders Python searches for an import, in order. |
| shadowing | A module found earlier on the search path hiding another with the same name. |
| installed copy | A package in `site-packages` that runs instead of the repository's source, because it was installed without `-e`. |
| editable install | An install that points at the repository folder, so edits to the source run. |
| project interpreter | The Python that the project's own commands use, not whatever `python` means in the terminal. |
| probe | A small command or file used to ask the interpreter or a type checker something, removed afterwards. |
| entry point | A place where the program starts: a script command, `__main__`, a route, a task, a test. |
| registration | Storing a function or class in a table, often by a decorator, so other code calls it without naming it. |
| dynamic use | A use that does not spell the name: by table, string, attribute name, fixture name, override or syntax. |
| blind spot | A kind of use a search cannot see, listed under *Not covered*. |
| indexed | Known to Sourcegraph, which can then search and navigate it. |
