# Submodules

**Verdict you produce:** the pinned commit before and after, and the
state of the working copy.

```
submodule: <path> from <url>
pinned:    <hash before> -> <hash after> (git ls-tree HEAD <path>)
checkout:  <git submodule status line>
verdict submodule: <updated and committed | initialised | moved | stopped: <why>>
```

The outer repository records one commit per submodule, not a branch.
`git ls-tree HEAD libs/lib` shows it:
`160000 commit f31d846...	libs/lib`.

## Status (lab: 2.43.0)

`git submodule status` prefixes each line:

| Prefix | Means |
| --- | --- |
| space | checked out at the pinned commit |
| `+` | checked out at another commit than the one pinned |
| `-` | not initialised (no files yet) |

A fresh clone without `--recurse-submodules` showed
`-91e11a6... libs/lib`.

## Commands

| Want | Command |
| --- | --- |
| files for every submodule, at the pinned commits | `git submodule update --init --recursive` |
| clone with them | `git clone --recurse-submodules <url>` |
| move a submodule to its remote branch's tip | `git submodule update --remote <path>`, then `git add <path>` and commit |
| see what the new pin brings | `git diff --submodule=log` (`Submodule libs/lib f31d846..91e11a6:` / `> lib v2`) |
| add one | `git submodule add <url> <path>` |
| move one | `git mv <old> <new>`; the new parent folder must exist (`mkdir` first: without it, `fatal: renaming 'libs/lib' failed: No such file or directory`); `.gitmodules` is updated |

After `update --remote` the lab status showed `+91e11a6... libs/lib`
and `git status` showed ` M libs/lib` until committed. Committing that is
the whole change: say the old and new hashes and the log between them.

Inside a submodule HEAD is detached (`HEAD detached at 91e11a6`). Work
there only on a branch (`git -C libs/lib switch -c <name>`), commit and
push it in the submodule's own repository first, then pin it in the
outer one.

## Local paths

A submodule from a local path or `file://` URL is refused since the
file protocol was restricted: `fatal: transport 'file' not allowed`.
`git -c protocol.file.allow=always submodule ...` allowed it in the lab.
It matters only for local copies (tests, bundles); GitLab URLs are
`https` or `ssh`.

## Never

- Never commit a `+` submodule line you did not mean to move; `git
  submodule update` (no `--remote`) puts it back to the pinned commit.
