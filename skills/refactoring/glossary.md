# Glossary

One sentence per term. Use these words and no synonyms.

| Term | Meaning |
| --- | --- |
| behaviour | Everything a caller can observe: return values, raised exceptions and their types, output written, calls made to the outside, and the names, parameters and defaults it can import and call. |
| refactoring | A change of structure that keeps behaviour, done as a sequence of steps. |
| step | One named change from the catalogue in `steps/`, small enough to check and commit on its own. |
| catalogue | The steps this skill knows, one file each in `steps/`, with preconditions, mechanics and traps. |
| shape | The architecture skill's end state for one layering violation (L1 to L11): a before, an after and a test both pass, in its `shapes/`. |
| recipe | The steps from a shape's before to its after, one file per violation ID in `recipes/`, each step a diff, a commit and its checks. |
| green | Every check in `core/checks.md` passes, with the same results as the baseline. |
| red | Any check fails, or gives a result the baseline did not. |
| baseline | The results of every check, and the probe output, recorded before the first edit. |
| pin | Make behaviour observable before changing code: tests that run it, a probe, or a golden master. |
| probe | Seniority's behaviour probe: a script that calls the code on fixed inputs and prints one line per result, run before and after and compared. |
| characterization test | A test whose expected value is what the code returns today, copied from its output, oddities included. |
| golden master | Many outputs of the code written to a file once, and compared with a fresh run after each step. |
| seam | A place where a test can change what the code uses without editing the code under test: a parameter, a module function, an object passed in. |
| sprout | New code written as a new, tested function or class, called from old code that stays untested. |
| wrap | New behaviour added around an old function by a new function that calls it, so the old one is unchanged. |
| public surface | Every name, parameter, default, module path, command-line option and stored or serialized name that code outside the change can rely on. |
| contract | The part of the public surface that other programs or stored data depend on: JSON field names, routes, stored fields, options, environment variables. |
| reference | Any place that names the thing being changed: code, a string, a patch target, `__all__`, config, packaging, docs. |
| hit | One line a search returned; a lead until read. |
| explained hit | A hit that is left unchanged on purpose, with the reason written down. |
| shim | Code left at the old name or path that forwards to the new one, so old callers keep working. |
| re-export | A shim of the form `from new import name as name` (or listed in `__all__`), which makes `old.name` import the moved object. |
| alias | A shim of the form `old_name = new_name` in the same module or class. |
| import-all | Running `tools/import_all.py`: import every module, resolve every dotted path in config files, import every script. |
| public names | The output of `tools/public_names.py`: each public name of a module with its kind and signature, to compare before and after. |
| red step | A step that turned a check red; it is undone, not patched. |
| undo | Put the working tree back to the last green commit, keeping the failed attempt in a stash. |
| finding | Something seen during a refactoring that is not acted on in it: a bug, an oddity, an improvement; reported with its evidence. |
| dead code | Code that nothing can reach, shown by searches, by what search cannot see ruled out, and by checks after removal. |
| untangle | Split a change that mixes structure and behaviour into commits that each hold one kind. |
