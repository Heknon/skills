# Where this skill comes from

Source: [temporalio/skill-temporal-developer](https://github.com/temporalio/skill-temporal-developer),
MIT licence (`LICENSE`, copyright Temporal Technologies Inc.).
Recorded commit: `3405710274f1d651cfc5022db2590fa7d6374b87` (2026-09-23).

## What was taken

| Here | Upstream | Changed |
| --- | --- | --- |
| `references/core/` | `references/core/` | no, word for word |
| `references/python/` | `references/python/` | no, word for word |
| `references/integrations.md` | `references/integrations.md` | only the Python rows kept; the steps that named other languages removed |
| `SKILL.md` | `SKILL.md` | Python only; "Working air gapped" added; the feedback note says to report from a connected machine |
| `LICENSE` | `LICENSE` | no |

Left out: the other languages (`references/{typescript,go,java,dotnet,ruby,rust}/`),
and the repository's own `README.md`, `CONTRIBUTING.md`, CI and
`pyproject.toml`.

## Updating

On a connected machine:

```
git clone https://github.com/temporalio/skill-temporal-developer upstream
git -C upstream log --oneline <recorded commit>..HEAD -- SKILL.md references/core references/python references/integrations.md
diff -r upstream/references/core   skills/temporal/references/core
diff -r upstream/references/python skills/temporal/references/python
```

Copy `references/core/` and `references/python/` over, filter
`integrations.md` to its Python rows again, carry any upstream change
in `SKILL.md` into this one by hand (keeping "Working air gapped"), and
record the new commit above. Check that no kept file links to a
language folder that is not here:
`grep -rnE "references/(typescript|go|java|dotnet|ruby|rust)/" skills/temporal`.
