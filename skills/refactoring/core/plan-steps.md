# Plan the steps

**Verdict you produce:** numbered steps, each named from the catalogue,
each leaving the code working, each with its check and its commit.

```
goal:  <the person's words>
pins:  <what is pinned first, and how>
1. <catalogue step>: <what moves where>; check: <checks>; commit: "<subject>"
2. ...
traps: <the traps from each step's file that apply here, and how the step avoids them>
not in this plan: <findings and improvements left out>
verdict plan: <n steps | stop: <why>>
```

A refactoring that cannot be stopped halfway is a rewrite. Every step
must leave the code working, so that if the work stops after any
commit, what is committed is correct and useful.

## Steps

1. **Name the end state** in one or two sentences: which names live
   where, which old names still import. Nothing else goes in.
2. **Pins come first.** If `core/before-you-start.md` said the code is
   not pinned, step 1 is **Pin** (`legacy/`), committed on its own.
3. **Make room before moving.** Create the new place first, empty or as
   a copy that is not used yet: turn a module into a package, add the
   new class, add the new function beside the old one. Then move callers
   to it, one group per step. Remove the old thing last, and only when
   `core/public-surface.md` says nothing outside uses it.
4. **One name or one section per step.** A step moves one function with
   what only it uses, or renames one name, or extracts one piece. If the
   diff of a step would touch more than a handful of files for more than
   one reason, cut it again.
5. **For each step, write the check that closes it** (`core/checks.md`),
   and which traps from its `steps/` file apply.
6. **Order by risk.** Steps that cannot break an import (extract a
   variable, extract a private function) before steps that can (move,
   rename, split).
7. **A tidy with no named result** (seniority's `core/scope.md` question
   6): list the candidate steps, keep only those that are structure, and
   put everything else (a changed default, a fixed rounding, a new
   exception) under `not in this plan` as a finding.
8. **For a Plan task, stop here.** Change no file; `git status` is clean
   when you answer.

## Common sequences

| Goal | Steps, in order |
| --- | --- |
| rename a public function | `steps/rename.md` with an alias left at the old name; callers in this repository moved to the new name; the alias removed only when asked |
| split a long module | `steps/split-module.md`: module to package (one step), then one section per step, re-exported from `__init__.py` |
| move a function to another module | `steps/move-function.md`: copy with its private helpers and constants, re-export at the old place, callers moved |
| turn module functions into a class | `steps/extract-class.md`: the class added unused; the functions made to delegate, sharing the same data; callers moved later if asked |
| change a widely used signature | `steps/change-signature.md`: new parameter with a default, or a new function beside the old; callers moved; the old form kept or removed when asked |
| shorten a long function | pin; then `steps/extract-variable.md` and `steps/extract-function.md`, one piece per step |
| untested code | `legacy/seams.md` for the smallest seam, `legacy/characterization.md`, then the steps above |
| move code towards an architecture shape (a service, a repository, a provider) | the recipe of the violation's ID (`recipes/README.md`): the new place added unused, callers switched, the old removed last |

## Never

- Never plan a step that leaves the code broken until a later step
  ("step 3 fixes the imports"). Each commit is green.
- Never put a behaviour change in the plan as a step. It is a finding,
  or a separate commit after the refactoring, asked for by name.
- Never plan the removal of a shim that callers outside this repository
  may use (`core/public-surface.md`).
