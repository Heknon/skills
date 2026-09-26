# Dependencies: add, pin, upgrade, resolve a conflict

**Verdict you produce:** the resolver's reason, the one requirement
changed and why, and the new lock.

```
error:    <the "Because ... and ..." lines, copied>
clash:    <requirement A> (from <file:line or package>) vs <requirement B> (from ...)
why each: <comment, issue, changelog, commit that put each bound there>
changed:  <one requirement, old -> new>
lock:     uv lock -> "Resolved <n> packages"; <package> now <version> (uv tree)
checked:  <tests run, and the result>
```

## Add, upgrade, remove

| To | Command (uv 0.12.19) |
| --- | --- |
| add | `uv add httpx` or `uv add "httpx>=0.28,<1"` (`core/metadata.md`) |
| upgrade one package inside its bounds | `uv lock --upgrade-package httpx` |
| upgrade everything inside the bounds | `uv lock --upgrade` (a large diff; only when asked) |
| see what would change, write nothing | `uv lock --dry-run` |
| see why a package is there | `uv tree --invert --package httpcore` |
| see the whole tree | `uv tree`, `uv tree --depth 1` |
| check the lock matches `pyproject.toml` | `uv lock --check` (same as `--locked`); exit 1 and `The lockfile at uv.lock needs to be updated` |
| remove | `uv remove httpx` |

`uv lock` keeps every locked version that still satisfies the
requirements. After changing an index or a source, a package already in
the lock may stay where it was until `--upgrade-package <name>` (lab:
`Updated acme-utils v9.0.0 -> v1.4.0` only then; `core/indexes.md`).

## Read a conflict

uv prints the chain of reasons. Lab, `httpx>=0.28` with `httpcore<1.0`:

```
error: No solution found when resolving dependencies
  cause: Because all versions of httpx depend on httpcore>=1.dev0 and your project depends on httpcore<1.0, we can conclude that your project and all versions of httpx are incompatible.
         And because your project depends on httpx==0.28.1, we can conclude that your project's requirements are unsatisfiable.
```

1. Name the two sides. Here: httpx (every version on the index) needs
   `httpcore>=1.dev0`; the project says `httpcore<1.0`. "all versions of
   httpx" means the versions the index has, not every version ever
   released.
2. Find why each bound exists: the comment beside it, `git log -L` on the
   line, the changelog, an incident note. A bound with a reason is a
   decision someone made.
3. Change the one requirement the reason allows. Here the note says the
   bug was fixed in httpcore 1.0.2, so `httpcore>=1.0.2` keeps the
   protection and lets httpx 0.28 in. If no reason allows a change, stop
   and ask with both sides named.
4. `uv lock`, then `uv tree --invert --package httpcore` to see the chosen
   version and who needs it, then the tests.

Other messages worth knowing (lab):

| Message | Means |
| --- | --- |
| `Because only acme-utils<=1.4.0 is available and your project depends on acme-utils>=2` | no version on the index satisfies the bound; check the index it looked at |
| `Because <x> was not found in the package registry` | the name is on no index uv read: a typo, the wrong index, or an explicit index without a source line |
| `hint: An index URL (...) could not be queried due to a lack of valid authentication credentials (401 Unauthorized)` | credentials missing (`uv/config.md`) |
| `Because only colorama{sys_platform == 'win32'}<0.4 is available and all versions of pytest depend on colorama{sys_platform == 'win32'}>=0.4` | the lock covers every platform: the mirror must hold Windows-only dependencies too |
| `has no wheels with a matching platform tag (e.g., win_amd64)` | a wheelhouse or index without the target's wheels (`core/across-the-gap.md`) |

## Never

- Never delete bounds until the lock passes. Every removed bound is a
  decision undone without its reason.
- Never use `--frozen` (install without checking the lock), `--no-deps`,
  or `override-dependencies` to get past a conflict.
- Never edit `uv.lock` by hand; change `pyproject.toml` and run `uv lock`.
- Never answer "which version is installed" from `pyproject.toml`: the
  lock (`uv/lockfile.md`) and `uv tree` say.
