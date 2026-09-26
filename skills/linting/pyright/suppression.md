# Suppressing pyright findings

**What it decides:** how to silence one pyright finding and find stale
ones. Verified on pyright 1.1.414; whether to suppress is in
`core/decide.md`.

## The forms

| Comment | Result in the lab |
| --- | --- |
| `# pyright: ignore[reportArgumentType]` | silences that rule on the line |
| `# pyright: ignore[reportArgumentType]  # reason` | the same; text after the bracket is fine with or without `#` |
| `# pyright: ignore[reportCallIssue]` on a `reportArgumentType` error | not silenced; with `reportUnnecessaryTypeIgnoreComment` on, also `Unnecessary "# pyright: ignore" rule: "reportCallIssue"` |
| `# pyright: ignore` | silences everything on the line |
| `# type: ignore`, and `# type: ignore[anything]` | silences everything on the line, whatever the brackets say, while `enableTypeIgnoreComments` is `true` (the default) |

So in a project that runs mypy and pyright, `# type: ignore[arg-type]`
silences a mypy code and, as a side effect, every pyright rule on that
line. When only pyright should be silenced, or the project runs only
pyright, use `# pyright: ignore[rule]`.

File-level: `# pyright: basic` or `# pyright: strict` on the first lines
changes the mode for that file (`pyright/strictness.md`); prefer that to
many line comments.

## Stale and blanket ignores

```toml
[tool.pyright]
reportUnnecessaryTypeIgnoreComment = "warning"
```

reports ignores that silence nothing, and wrong rules in brackets. It is
off by default in every mode tried, strict included. Suggest it; set it
when asked.
