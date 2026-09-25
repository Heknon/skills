# API reference from docstrings

**What it decides:** how a page shows a Python module's API from its
docstrings, so the reference is generated and never retyped.

mkdocstrings with its Python handler reads the source files without
importing them (through griffe), and renders each object's signature and
docstring. It works the same under MkDocs and Zensical. Tested with
mkdocstrings 1.0.6 and mkdocstrings-python 2.0.9.

## On a page

One line per module or object, the dotted path as you would import it:

```markdown
# Billing API

::: billing.charges
```

Confirm the dotted path with navigation (Resolve) before writing it.

## In mkdocs.yml

```yaml
plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          paths: [src]
          options:
            docstring_style: google
```

- **`paths`** is where the package folder lives, relative to
  `mkdocs.yml`. For a `src` layout (`src\billing\__init__.py`) it is
  `[src]`; for a flat layout (`billing\__init__.py` next to
  `mkdocs.yml`) it is `[.]`. In a combined site it points at the other
  repository's checkout, such as `[../billing/src]`.
- **`docstring_style`** must match how the repository writes docstrings:
  `google` (sections `Args:`, `Returns:`, `Raises:`), `numpy` (sections
  underlined with dashes), or `sphinx` (`:param x:` lines). The default is
  `google`. A wrong style renders sections as plain text and does not
  warn.

## What it hides by default

- **Objects with no docstring are left out** (`show_if_no_docstring`
  defaults to false). A public function without a docstring is missing
  from the reference, and nothing warns. An Audit counts these as
  undocumented surfaces.
- **Names starting with one underscore are left out** (the default
  filter `!^_[^_]`).
- Source code is shown under each object (`show_source` defaults to
  true).

## When it fails

| Message | Fix |
| --- | --- |
| `mkdocstrings: x.y could not be found` | wrong dotted path, or `paths` does not reach the package folder |
| `griffe: file.py:N: Parameter 'a' does not appear in the function signature` | the docstring names a parameter that does not exist; fix the docstring |

Both fail the MkDocs strict build. Zensical 0.0.65 fails on the first,
but only prints the second and passes (`site.md`).
