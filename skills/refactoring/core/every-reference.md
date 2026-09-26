# Every reference

**Verdict you produce:** the list of every hit for the old name or path,
each edited or explained, and the proof that none was missed.

```
searched:  <each pattern and where: all files | *.py | config>
hits:      <n> lines in <m> files
  <path:line>  <kind>  edit | leave: <why>
after:     <the same searches: only the explained hits remain>
proof:     <checks run (core/checks.md), and the probe call for each dynamic hit>
not seen:  <what search cannot reach: other repositories, stored data, ...>
verdict references: <complete | incomplete: <what is left>>
```

Your editor has no rename-symbol and no find-references. A rename or a
move is complete only when you have found every reference by search,
and a check that fails on a miss has run. The searches themselves are
the navigation skill's (`skills/navigation/core/search-patterns.md`,
`core/trace-in.md`, `core/what-search-misses.md`); this file says what a
rename or move must search for, what it must change, and how to prove
the list complete.

## Steps

1. **Write the forms to search**, for the name `get_user` in the module
   `app.users`:

   | Form | Pattern |
   | --- | --- |
   | the name as a word, anywhere | `\bget_user\b` |
   | for a move, the module as a dotted path | `app\.users\b` |
   | for a move, the module as a file path | `app/users`, and `app\\users` in Windows files |
   | the module imported from its package | `from app import .*\busers\b` (the lab's `profile.py` and `lookup.py` used this form, which `app\.users` does not match) |
   | relative imports of the module | `from \.+users import`, `from \. import .*\busers\b` |
   | the module imported under another name | `import app\.users as`, then that name in the file |
   | the name built from parts | the parts in quotes (`"get_"`), `getattr\(`, `import_module\(`, `__import__\(` |

2. **Search all files, not only `*.py`.** Configuration, packaging, docs,
   CI files and scripts name code too. In the editor, `grep` with no file
   filter, then with `**/*.py`. In the terminal, `git grep` searches the
   tracked files, skips binary ones with `-I`, and matches whole words
   with `-w` (where `_` counts as part of a word):

   ```powershell
   git grep -n -w -I get_user
   git grep -n -w -I --untracked get_user     # also files not yet added
   git grep -n -I -e "app\.users" -e "app/users"
   ```

   In the lab, `git grep -n -w -I get_user` found 14 lines in 8 files:
   the definition, a call inside the module, `__all__`, a call in another
   module, a `getattr` string, a YAML job, two doc lines, a test import,
   two test calls, a `mock.patch` string, and another class's method of
   the same name with its test.
3. **Go through navigation's `core/what-search-misses.md`**, all eleven
   items, for the name. Each one applies and was searched, or does not
   apply.
4. **Read every hit and write it on the list** with its kind and a
   decision:

   | Hit | Decision |
   | --- | --- |
   | the `def` or `class` line, calls, imports | edit |
   | `__all__` entries | edit (ruff `F822` catches a miss, mypy does not) |
   | patch targets: `mock.patch("app.users.get_user")`, `monkeypatch.setattr("...")`, `mocker.patch` | edit; after a move, to where the name is used (pytest's `core/mocking.md`) |
   | strings: `getattr(obj, "get_user", None)`, a dispatch table keyed by name, `import_module("app.users")` | edit, and add a probe call that goes through it: with a default, a miss fails silently |
   | dotted paths in YAML, TOML, INI, JSON, logging config | edit, unless another deployment owns that file: then a shim |
   | `[project.scripts]`, `[project.entry-points]` | edit and reinstall (`steps/move-function.md`), or keep a shim |
   | CI files, Dockerfiles, scripts: `python -m app.users`, `--cov=app/users` | edit |
   | docs, README, docstrings, comments | edit |
   | the same word meaning another thing: another class's method, a local variable, a JSON key | leave, and say what it is |
   | a serialized, stored or wire name | stop: a contract (`core/before-you-start.md`) |
   | generated or vendored code | leave; regenerate it the project's way |
   | test function names, such as `test_get_user_found` | edit or leave; say which |

5. **Edit** each `edit` hit (`core/step-loop.md`).
6. **Search again** with every pattern of step 1. What remains must be
   exactly the `leave` hits. In the lab, 14 hits became 3, all of them
   `AdminClient.get_user` and its test and doc line.
7. **Run the check that fails on a miss**: `core/checks.md` in full,
   with `tools/import_all.py --config` on every config file that had a
   hit, and a probe line for every dynamic hit. In the lab, after a
   rename that edited the definition, the calls and the test import, the
   tests failed only on the `mock.patch` string; ruff found only
   `__all__`; mypy found nothing; `import_all.py --config
   config/jobs.yaml` found the YAML job; and nothing but a probe call of
   `resolve(1)` showed the `getattr` string, which returned
   `{'id': 1, 'name': 'unknown'}` instead of Ada.
8. **Name what search cannot reach** under `not seen`: other
   repositories (Sourcegraph, when connected, per navigation's
   `tools/sourcegraph.md`), stored data, other teams' tests that patch
   the old name. These decide the shim (`core/public-surface.md`).

## Never

- Never search only `*.py`: in the lab the YAML job and the docs page
  were invisible to it.
- Never decide a hit from the search line alone; read the line in its
  file (navigation's invariant 1).
- Never call a rename complete because the tests pass: in the lab they
  passed with the `getattr` string, the YAML path and the docs all
  still naming the old function.
