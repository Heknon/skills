# Zed's diagnostics panel

**Verdict you produce:** which checker produced a finding in the panel,
whether CI runs that checker with those settings, and what the finding
means for the code.

```
panel:    basedpyright (Zed's default), typeCheckingMode "standard" set by Zed
ci:       ruff check, mypy (from .gitlab-ci.yml): both clean here
finding:  "strip" is not a known attribute of "None": real, feed_title([]) raises AttributeError
          Cannot access attribute "page_size": runtime attribute set by load(); not a bug
```

CI is the standard; the panel is a hint. A hint can still be a bug
nobody else checks for, so read each one.

## What Zed runs for Python

Read in Zed 1.21.0's source (`assets/settings/default.json`,
`crates/languages/src/python.rs`); Zed itself was not run in the lab.

| Server | By default | Which binary | Settings Zed adds |
| --- | --- | --- | --- |
| basedpyright | on | `basedpyright-langserver` on `PATH`, else an npm install Zed manages | `typeCheckingMode: "standard"` unless your Zed settings set one; import sorting off |
| ruff | on | `ruff` next to the selected Python environment's interpreter, else `ruff` on `PATH`, else a download from GitHub | also the formatter, and `source.organizeImports.ruff` on format |
| ty, pyrefly, pyright, pylsp | off | | |

The default list is
`"language_servers": ["basedpyright", "ruff", "!ty", "!pyrefly", "!pyright", "!pylsp", "..."]`:
a name starts a server, `!name` stops it, `"..."` means the rest.

Consequences:

- **basedpyright is not mypy.** It checks the bodies of unannotated
  functions, which mypy skips unless `check_untyped_defs = true`.
  *Lab:* `mypy` said `Success` on a file where basedpyright in standard
  mode reported two errors, one of them a real crash.
- **Air gapped**, a server Zed must download may never start; the
  panel then shows nothing from it, which is not a pass.
- **The ruff in the panel** is the project's only when Zed has the
  project's `.venv` selected; otherwise it may be a global one of
  another version (`core/run-like-ci.md`).

## When the panel and CI disagree

1. Name what CI runs (the CI file) and run it the same way.
2. Name the panel's checker from the message style: basedpyright and
   pyright end with `(reportXxx)`; ruff shows a code such as `F401`.
3. For each finding, decide whether it is true at runtime (run the case)
   and whether CI would see it with its settings.
4. Fix real bugs as a behaviour decision. Leave the rest, and say so.
5. If the person wants the panel to match CI, offer one of these, and do
   it only when asked:
   - a project `.zed/settings.json` choosing the servers, in the syntax
     above, such as `{"languages": {"Python": {"language_servers":
     ["ruff", "!basedpyright", "..."]}}}`;
   - making CI stricter (`check_untyped_defs = true` in `[tool.mypy]`
     found both problems in the lab), which is an adoption task
     (`core/adopt.md`).

## Never

- Never rewrite code or add `# pyright: ignore` only to empty the panel.
- Never report "no errors" from the panel alone; run the checker.
