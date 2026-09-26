# Conventions: messages, trailers, names

Defaults for when the repository has none (`core/name.md` finds it
first). Checked on git 2.43.0 unless marked.

## Commit message defaults

```
Round VAT to cents                          <- subject: imperative, capitalised,
                                               no full stop, <= 50 aimed, 72 max
Invoices showed amounts like 3.8000000000000003
because the VAT was never rounded.          <- body: why, and what changes for
                                               a user; wrap at 72
Refs PROJ-311                               <- references and trailers last
```

- One `-m` per paragraph: `git commit -m "<subject>" -m "<body>" -m
  "Refs PROJ-311"` gave exactly the three paragraphs above, separated by
  blank lines.
- A body longer than a line or two: write `msg.txt` with the editing
  tool and `git commit -F msg.txt`. A UTF-8 byte order mark stays in the
  subject (lab: the subject began with bytes `357 273 277`); a UTF-16
  file is refused: `error: a NUL byte in commit log message not
  allowed.`

## Conventional Commits

`type(scope)!: subject`, lower case after the colon, no full stop. Use
only the types and scopes in `git log` or the tool's config. A repository
using commitlint's `config-conventional` showed `feat`, `fix`, `docs`,
`chore`, `refactor`, `test`. A breaking change: `!` after the type or
scope, and a `BREAKING CHANGE: <what>` paragraph at the end.

## Trailers

Git parses a trailer only as `Key: value` in the last paragraph:

| Want | Command | Lab result |
| --- | --- | --- |
| add one | `git commit ... --trailer "Refs: PROJ-311"` | a `Refs: PROJ-311` paragraph |
| read them | `git log -n 30 --format='%(trailers:only)'` | empty for `Refs PROJ-302` (no colon) |
| one key's values | `git log -1 --format='%(trailers:key=Refs,valueonly)'` | `PROJ-311` |
| co-author | `-m "Co-authored-by: Name <email>"` as the last paragraph | |

Copy the repository's form exactly, colon or not.

Which words close an issue when a merge request merges (`Closes #12`,
`Fixes PROJ-12`) is a GitLab project setting: to verify on GitLab 19.4;
the deployment skill reads project settings through the API.

## Branch names

| Rule | Checked with `git check-ref-format --branch` |
| --- | --- |
| no spaces | `fix/PROJ-42 discount renewals`: refused |
| no `..` | `fix/PROJ-42..renewals`: refused |
| no `.lock` ending | `fix/PROJ-42-x.lock`: refused |
| no leading `-` | `-fix`: refused |
| capitals allowed by git | `fix/PROJ-42-Discount`: accepted; still avoid |
| no branch named like a folder of another | a branch `fix` blocks `fix/x`: `cannot lock ref` |

Default pattern: `<type>/<issue>-<slug>` with types `feat`, `fix`,
`chore`, `docs`, `refactor`.

## Tags

`v<major>.<minor>.<patch>`, annotated. `git tag -l --sort=-v:refname`
sorts by version: `v1.10.0` before `v1.9.1` before `v1.2.0` (lab).

## A formatting commit

A formatting sweep is its own commit (the linting skill decides when).
Record it so blame skips it:

```
.git-blame-ignore-revs:
# Format billing and utils
c2a40280...  (the full hash)
```

`git blame --ignore-revs-file .git-blame-ignore-revs -L 12,13 billing.py`
then showed the older commit instead of the formatting one (lab). Setting
`blame.ignoreRevsFile` in configuration is proposed, never written
unasked.
