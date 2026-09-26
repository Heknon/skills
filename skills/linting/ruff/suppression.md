# Suppressing ruff findings

**What it decides:** which comment silences what, and how to find
suppressions that hide too much. Verified on ruff 0.16.9; the reason for
suppressing at all is in `core/decide.md`.

## The forms

| Comment | Silences | Lab |
| --- | --- | --- |
| `# noqa: F401` | that code on that line | works; a reason may follow: `# noqa: F401  # re-exported for plugins` |
| `# noqa: F401, E501` | both codes on that line | works; an unused one is reported by `RUF100` |
| `# noqa` | **every** code on that line | `PGH004 Use specific rule codes when using noqa` |
| `# noqa F401` (no colon) | **every** code on that line | `PGH004 Use a colon when specifying noqa rule codes` |
| `# noqa: unused-import` | nothing: names are not accepted | `warning: Invalid # noqa directive ... expected a comma-separated list of codes` |
| `# ruff: noqa: F401` at the top of a file | that code in the whole file | works |
| `# ruff: noqa` at the top of a file | **every** code in the whole file | it hid an `F821 Undefined name`, a real bug; `PGH004` flags it |
| `# ruff: ignore[F401]` | that code on that line | works on 0.16.9; `# ruff: ignore[unused-import]` did not |
| `# ruff: disable[E501]` ... `# ruff: enable[E501]` | that code between the two lines | works; without `enable`, `RUF104` (unmatched) and it runs to the end of the scope |

In `__init__.py`, prefer declaring the re-export over suppressing:
`from shop.pricing import price as price`, or `__all__ = ["price"]`.
Both are what `ruff rule F401` recommends, and both passed in the lab.

## Checks on the suppressions themselves

| Rule | Reports |
| --- | --- |
| `RUF100` | a `noqa` or `ruff: ignore` that suppresses nothing (`Unused noqa directive (unused: E501)`, `Unused suppression`) |
| `RUF101` | a `noqa` that uses an old code (`TCH003 is a redirect to TC003`) |
| `RUF102` | an unknown code (`Invalid rule code in # noqa: F999`) |
| `RUF103` | a malformed `# ruff:` comment (`Invalid suppression comment`) |
| `RUF104` | a `# ruff: disable` without its `enable` |
| `PGH004` | blanket `noqa` and `ruff: noqa` |

Suggest these to a team that uses many suppressions; add them to
`select` only when asked. `ruff check --ignore-noqa` shows what every
`noqa` hides, without editing files.

## Adding suppressions in bulk

`ruff check --add-noqa[=<reason>]` writes `# noqa: <codes>` on every
failing line (`Added 3 noqa directives.`); with `--add-noqa="legacy"`
the lab got `# noqa: F401 legacy`. `--add-ignore[=<reason>]` does the
same with `# ruff: ignore[...]`. Both are a baseline for legacy code,
used only when the person asks for one (`core/adopt.md`); on a line
that already had a bare `# noqa`, `--add-noqa` left it bare.
