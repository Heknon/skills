# Reading pyright's output

**What it decides:** what a pyright finding says and how severe it is.
Verified on pyright 1.1.414 and basedpyright 1.40.1.

## The shape

```
/abs/path/src/app/core.py
  /abs/path/src/app/core.py:10:17 - error: Argument of type "str | None" cannot be assigned to parameter "name" of type "str" in function "greet"
    Type "str | None" is not assignable to type "str"
      "None" is not assignable to "str" (reportArgumentType)
  /abs/path/src/app/core.py:11:17 - information: Type of "user" is "str | None"
3 errors, 0 warnings, 1 information
```

- A file header, then `path:line:col - severity: message`, indented
  explanation lines, and the rule in brackets at the end.
- Severities: `error`, `warning`, `information`. basedpyright says
  `note` for information and in its summary.
- Exit code 1 when there are errors; warnings alone exit 0 unless
  `--warnings` is given (*lab*). `--level error` hides warnings.
- `--outputjson` gives `file`, `severity`, `message`, `rule` and a
  `range` whose `line` counts from **0** (line 17 in the text output was
  `"line": 16`), with a `summary` of counts.

## Rules seen in the lab

| Rule | Message starts | Note |
| --- | --- | --- |
| `reportArgumentType` | `Argument of type "X" cannot be assigned to parameter` | mypy's `arg-type` |
| `reportReturnType` | `Type "bytearray" is not assignable to return type "bytes"` | pyright does not promote `bytearray` (`disableBytesTypePromotions`) |
| `reportOperatorIssue` | `Operator "+" not supported for types` | found inside an unannotated function mypy skipped |
| `reportOptionalMemberAccess` | `"strip" is not a known attribute of "None"` | a real crash in the lab |
| `reportAttributeAccessIssue` | `Cannot access attribute "page_size" for class "Settings"` | an attribute set at runtime |
| `reportCallIssue` | `No parameter named "name"` | pydantic alias without a plugin (`mypy/pydantic.md`) |
| `reportMissingImports` | `Import "x" could not be resolved` | not in pyright's environment (`pyright/install.md`) |
| `reportUnknownParameterType`, `reportMissingParameterType`, `reportUnknownVariableType`, `reportUnknownArgumentType` | `Type of parameter "x" is unknown`, `Type annotation is missing for parameter "x"` | strict mode, or basedpyright's default mode |
| `reportUnnecessaryTypeIgnoreComment` | `Unnecessary "# pyright: ignore" rule: "reportArgumentType"` | off unless configured |

The rule name describes the check; pyright has no command that
explains a rule. For which environment and config it used, run with
`--verbose`.

## pyright and mypy disagree

They are different checkers with different defaults. In the lab pyright
checked unannotated functions (mypy does not by default), rejected
`bytearray` as `bytes` (mypy 2.x too, 1.x not), and read pydantic
models without a plugin. Decide by what CI runs (`core/run-like-ci.md`).
