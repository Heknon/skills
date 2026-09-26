# `type: ignore` in mypy

**What it decides:** how to silence one mypy error, and how to find
ignores that are wrong or stale. Verified on mypy 2.3.1; whether to
suppress at all is in `core/decide.md`.

## The form

```python
value = greet(raw)  # type: ignore[arg-type]  # the stub for greet is wrong, see issue 42
```

What the lab showed, on one file, with `--warn-unused-ignores
--enable-error-code ignore-without-code`:

| Comment | Result |
| --- | --- |
| `# type: ignore[arg-type]` on an `arg-type` error | silenced |
| `# type: ignore[assignment]` on an `arg-type` error | not silenced: `Unused "type: ignore" comment  [unused-ignore]`, the error, and `note: Error code "arg-type" not covered by "type: ignore[assignment]" comment` |
| `# type: ignore[arg-type]` on a line with no error | `Unused "type: ignore" comment  [unused-ignore]` |
| `# type: ignore` | silences everything; `"type: ignore" comment without error code (consider "type: ignore[arg-type]" instead)  [ignore-without-code]` |
| `# type: ignore[arg-type]  # stub is wrong` | silenced; the reason is fine after its own `#` |
| `# type: ignore[arg-type] stub is wrong` | `Invalid "type: ignore" comment  [syntax]`, and the error is not silenced |
| `# noqa: E501  # type: ignore[arg-type]` | not silenced: mypy reads the ignore only as the first comment |

So: the code in brackets, the reason after `  # `, and the `type:
ignore` first on the line.

## Finding ignores that hide too much

| Setting | Reports |
| --- | --- |
| `warn_unused_ignores = true` (part of `strict`) | ignores that silence nothing, or the wrong code |
| `enable_error_code = ["ignore-without-code"]` | bare `# type: ignore` |
| ruff's `PGH003` (blanket-type-ignore) | bare `# type: ignore`, from ruff instead of mypy |

Suggest them; add them to a project when asked.

## Other ways to silence, and why they are wider

| Form | Scope |
| --- | --- |
| `ignore_errors = true` in an override | every error in those modules |
| `disable_error_code = ["..."]` | that code everywhere |
| `cast(T, x)` | tells mypy `x` is `T`, checked by nobody; `warn_redundant_casts` catches only casts to the type it already has |

A `cast` or `Any` is a suppression that does not look like one; treat it
the same way (`core/decide.md`).
