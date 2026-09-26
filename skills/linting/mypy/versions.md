# mypy 2.x against 1.x

Check first: `uv run --no-sync mypy --version`. Compared in the lab:
mypy 2.3.1 and 1.20.2, the same files, the same config; defaults read
from `mypy.options.Options()` in each.

| Topic | 1.20.2 | 2.3.1 |
| --- | --- | --- |
| `bytearray` and `memoryview` where `bytes` is expected | accepted by default; `--strict-bytes` (part of `--strict`) rejects | **rejected by default**: `Incompatible return value type (got "bytearray", expected "bytes")`; `--no-strict-bytes` for the old behaviour |
| `--allow-redefinition` | an alias of `--allow-redefinition-old` | the new, more flexible semantics; `--allow-redefinition-new` is a deprecated alias |
| effect of `--allow-redefinition` on one sample | `Success` | a new error: `Incompatible types in assignment (expression has type "int", variable has type "None")` for a class attribute set to `None` then assigned in a method |
| `local_partial_types` default | `False` | `True` (no difference on the lab's samples) |
| `--native-parser` | missing | present (off unless given) |
| `-n`, `--num-workers`, `MYPY_NUM_WORKERS` | missing | present, marked experimental |
| `--enable-incomplete-feature` choices | `InlineTypedDict`, `PreciseTupleTypes`, `TypeForm` | `InlineTypedDict`, `PreciseTupleTypes` |
| config discovery, `strict` in overrides, error codes and messages used in this skill | same | same |

## A 1.x project moving to 2.x

1. Run 2.x once and diff the error lists; the `bytes` change is the
   usual source of new errors.
2. For each new error, fix the code (convert with `bytes(...)`) or, if
   the team decides to keep the old rule for now, set
   `strict_bytes = false` in `[tool.mypy]` with a comment.
3. If the config uses `allow_redefinition`, rerun with and without it
   and read what changed.
4. Upgrade the pin in the dev group as its own change (packaging owns
   the groups); CI and pre-commit then follow the lock.

## Writing for both

Stay on 1.x settings that mean the same on both: set `strict_bytes`
explicitly, avoid `allow_redefinition`, and run the suite of checks on
each (`uv run --with "mypy==1.20.2" mypy ...`,
`uv run --with "mypy==2.3.1" mypy ...`), as the pytest skill does for
pytest.
