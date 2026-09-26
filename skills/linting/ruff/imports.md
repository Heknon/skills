# Import sorting with ruff

**What it decides:** how imports are sorted and grouped, in place of
isort. Verified on ruff 0.16.9.

## The facts

- Import sorting is a lint rule, `I001` (`unsorted-imports`), not part
  of the formatter. *Lab:* `ruff format --diff` on a file with unsorted
  imports said `1 file already formatted`.
- `I001` is in ruff 0.16.9's default rule set; on 0.15.8 it was not
  (`ruff/rules.md`). A project that pins `select` needs `"I"` in it.
- The fix is safe when nothing but imports moves:
  `uv run --no-sync ruff check --select I --fix <file>` sorts one file.
  Use `--diff` first to see it.
- Zed runs `source.organizeImports.ruff` when it formats a Python file
  (Zed 1.21.0 default settings, read, not run), so saving in Zed can
  reorder imports in files the task did not otherwise touch.

## Groups and first-party code

ruff writes standard library, third-party and first-party imports as
separate blocks. It decides first-party from `src` (default: the
project folder and `src/`) and `lint.isort.known-first-party`.

*Lab:* with the package in `lib/other/`, outside `src`, `import other`
was sorted into the third-party block, next to `pydantic`:

```
import os

import other
import pydantic
```

With `known-first-party = ["other"]` it got its own block:

```toml
[tool.ruff.lint.isort]
known-first-party = ["other"]
```

```
import os

import pydantic

import other
```

In a monorepo, list the sibling packages that are first-party for the
member, or set `src` to their folders.

## Options

`uv run --no-sync ruff config lint.isort` lists them (`known-first-party`,
`known-third-party`, `force-single-line`, `combine-as-imports`,
`section-order`, `lines-after-imports`, and more), and
`ruff config lint.isort.<option>` explains one. Copy an old isort
setting only after finding the same name there; do not assume isort's
option names.

## Moving from isort

1. Find isort's settings (`[tool.isort]`, `.isort.cfg`, `setup.cfg`).
2. Map each to a `lint.isort` option that `ruff config` shows; note any
   with no equivalent.
3. Add `"I"` to `select`, run `ruff check --select I --diff .` and look
   at the size. The re-sort of the whole repository is a formatting-only
   commit (`core/in-scope.md`).
4. Remove isort from the dev group and the hooks in the same change.
