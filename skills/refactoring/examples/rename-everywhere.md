# Worked example: a rename proven complete

Kind: Step (rename). Outputs from a lab run on Python 3.12.14, pytest
9.1.1, ruff 0.16.9, mypy 2.3.1, git 2.43.0, commands run in PowerShell
7.5 on Linux.

## The ask

> Rename get_user to fetch_user in app/users.py, everywhere it's used.

## Steps

1. **Before you start** (`core/before-you-start.md`). `get_user` returns
   a dict to Python callers; it is not a field, route or option. Baseline:

   ```
   uv run --no-sync pytest -q          -> 6 passed in 0.03s
   uv run --no-sync ruff check app tests -> All checks passed!
   uv run --no-sync mypy app tests       -> Success: no issues found in 9 source files
   ```

   The probe, `.ledger/probe.py`, calls the code through each path found
   in step 2, including the `getattr` and the YAML job:

   ```python
   import sys
   sys.path[:0] = ["", "src"]

   from app import jobs, lookup, profile, users

   print("list_users", users.list_users(), users.list_users(active_only=True))
   print("display_name", profile.display_name(1), profile.display_name(99))
   print("resolve", lookup.resolve(1), lookup.resolve(99))
   print("job audit_user", jobs.run("audit_user", 2))
   ```

   ```
   resolve {'id': 1, 'name': 'Ada', 'active': True} {'id': 99, 'name': 'unknown'}
   job audit_user {'id': 2, 'name': 'Linus', 'active': False}
   ```

   Public names of `app.users` saved to `.ledger/names-before.txt`.
2. **Every reference** (`core/every-reference.md`), all files:

   ```powershell
   git grep -n -w -I get_user
   ```

   | Hit | Kind | Decision |
   | --- | --- | --- |
   | `app/users.py:11` | definition | edit |
   | `app/users.py:17` | call in the module | edit |
   | `app/users.py:3` | `__all__` | edit, keep the old name too (alias) |
   | `app/profile.py:5` | call through `users.` | edit |
   | `app/lookup.py:10` | `getattr(source, "get_user", None)` | edit; silent if missed |
   | `config/jobs.yaml:3` | dotted path | edit |
   | `docs/users.md:3` | docs | edit |
   | `tests/test_users.py:4, 8, 12` | import and calls | edit |
   | `tests/test_users.py:20` | `mock.patch("app.users.get_user")` | edit |
   | `app/admin.py:8`, `tests/test_admin.py:5`, `docs/users.md:6` | `AdminClient.get_user`, a different method | leave |

   14 lines in 8 files. `from app import users` (the form `profile.py`
   and `lookup.py` use) was searched too; no other form turned up.
3. **Shim** (`core/public-surface.md`). No build system or README says
   who installs `app`, so it is unknown whether anything outside imports
   `get_user`: keep an alias.

   ```python
   def fetch_user(user_id: int) -> dict[str, object] | None:
       """Return the user with this id, or None."""
       return _STORE.get(user_id)


   get_user = fetch_user  # old name, kept for callers outside this repository
   ```

4. **Edit** every `edit` hit, one by one; `AdminClient` untouched.
5. **Search again**: only the explained hits remain.

   ```
   app/admin.py:8:    def get_user(self, login: str) -> str | None:
   app/users.py:3:__all__ = ["fetch_user", "get_user", "list_users"]
   app/users.py:16:get_user = fetch_user  # old name, kept for callers outside this repository
   docs/users.md:6:For admins, use `AdminClient.get_user(login)` in `app/admin.py`; it reads
   tests/test_admin.py:5:    assert AdminClient({"root": "Root"}).get_user("root") == "Root"
   ```

6. **Checks** (`core/checks.md`):

   ```
   6 passed in 0.03s
   All checks passed!
   Success: no issues found in 9 source files
   OK   config/jobs.yaml: app.users.fetch_user
   import_all: 8 ok, 0 failed, 1 skipped
   probe diff exit: 0
   +app.users.fetch_user  function  (user_id: int) -> dict[str, object] | None
   ```

   The names comparison only added a line.
7. **Commit**: `git add -- app/users.py app/profile.py app/lookup.py
   config/jobs.yaml docs/users.md tests/test_users.py`, `6 files changed,
   14 insertions(+), 11 deletions(-)`, then
   `git commit -m "Rename get_user to fetch_user" -m "Structure only. get_user stays as an alias of fetch_user for callers outside this repository."`:
   `b7c02a3 Rename get_user to fetch_user`.

## What the checks alone would have missed

An earlier run of the same rename edited only the definition, the
calls and the test import. The tests failed on the patch string
(`AttributeError: <module 'app.users' ...> does not have the attribute
'get_user'`), ruff found `F822` in `__all__`, and mypy passed. With those
two fixed, everything was green, while `resolve(1)` returned
`{'id': 1, 'name': 'unknown'}` and the YAML job would have failed at 2
a.m. Only the search list and the probe showed both.

## The answer

```
## Steps
1. rename: get_user -> fetch_user in app.users, alias kept.
   b7c02a3 Rename get_user to fetch_user. pytest 6 passed; ruff All checks
   passed!; mypy Success: no issues found in 9 source files; import_all 8 ok,
   0 failed; probe identical.

## References
git grep -n -w -I get_user: 14 lines in 8 files before, 5 after.
Edited: app/users.py:3,11,17; app/profile.py:5; app/lookup.py:10 (getattr
string); config/jobs.yaml:3; docs/users.md:3; tests/test_users.py:4,8,12,20
(import, calls, mock.patch target).
Left: app/admin.py:8, tests/test_admin.py:5, docs/users.md:6:
AdminClient.get_user, another method. app/users.py:3,16: the alias.

## Behaviour
Tests 6 passed before and after; the probe (list_users, display_name,
resolve through getattr, the YAML job) identical; public names of app.users
only gained fetch_user.

## Findings
none
```

Then seniority's headings; under *Unverified*: callers in other
repositories were not searched, which is why the alias stays; tests
elsewhere that patch `app.users.get_user` would no longer reach code that
calls `fetch_user`.
