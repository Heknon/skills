# Collection

Collection builds a tree of **nodes** from the paths given, then a flat
list of **items** (tests) to run.

## The tree (*lab*, `uv run pytest --co`, same on 8.4.2 and 9.1.1)

```
<Dir tree>                      rootdir-relative directories (Dir, since 8.0)
  <Dir tests>
    <Package pkg>               a directory with __init__.py
      <Module test_m.py>
        <Class TestA>
          <Function test_x>     an item
    <Module test_top.py>
      <Function test_y>
```

| Class | What it is |
| --- | --- |
| `Session` | the root; `session.items` after collection |
| `Dir`, `Package` | directories; `Package` when it has `__init__.py` |
| `Module` | a Python test file (`python_files`, default `test_*.py` and `*_test.py`) |
| `Class` | a class matching `python_classes` (default `Test*`) without `__init__` |
| `Function` | a test function or method (`python_functions`, default `test*`); one per parametrized case |
| `File`, `Item`, `Collector` | base classes for your own collectors and items |

Every node has `name`, `nodeid` (`tests/pkg/test_m.py::TestA::test_x`),
`path`, `parent`, `config`, `session`, `stash`, `iter_markers()`,
`get_closest_marker(name)`, `add_marker()`, `listchain()` (root to
node), and `ihook` (hooks filtered to its conftests).

## How it walks

1. `pytest_collection(session)` → `session.perform_collect()`.
2. For each argument, directories are collected with
   `pytest_collect_directory`; each entry is checked with
   `pytest_ignore_collect` (`--ignore`, `--ignore-glob`,
   `collect_ignore` in a conftest, `norecursedirs`).
3. Each file goes to `pytest_collect_file`; pytest's python plugin
   returns a `Module` through `pytest_pycollect_makemodule` for matching
   names.
4. `Module.collect()` imports the module (`internals/config-and-conftests.md`,
   import modes), then calls `pytest_pycollect_makeitem` for each name.
   Test functions go through `pytest_generate_tests(metafunc)`, which is
   where `@pytest.mark.parametrize` and fixture `params` become one
   `Function` per case.
5. Each result is reported with `pytest_collectreport`; an import error
   in a module is a failed collect report ("ERROR collecting"), which
   stops the run before any test (`Interrupted: 1 error during
   collection`) unless `--continue-on-collection-errors`.
6. `check_pending()` validates hook names, then
   `pytest_collection_modifyitems(session, config, items)` may reorder or
   remove items in place, then `pytest_collection_finish`.

## Custom collector and item (*lab*, both versions)

For tests stored in non-Python files, one test per line of `test_*.cases`
(`name | expression | expected`):

```python
import pytest

def pytest_collect_file(parent, file_path):
    if file_path.suffix == ".cases" and file_path.name.startswith("test"):
        return CasesFile.from_parent(parent, path=file_path)

class CasesFile(pytest.File):
    def collect(self):
        for lineno, line in enumerate(self.path.read_text().splitlines(), 1):
            name, expr, expected = [p.strip() for p in line.split("|")]
            yield CaseItem.from_parent(self, name=name, expr=expr, expected=expected, lineno=lineno)

class CaseMismatch(Exception):
    pass

class CaseItem(pytest.Item):
    def __init__(self, *, expr, expected, lineno, **kwargs):
        super().__init__(**kwargs)
        self.expr, self.expected, self.lineno = expr, expected, lineno

    def runtest(self):
        got = str(eval(self.expr))
        if got != self.expected:
            raise CaseMismatch(got)

    def repr_failure(self, excinfo):
        if isinstance(excinfo.value, CaseMismatch):
            return f"{self.expr} gave {excinfo.value.args[0]}, expected {self.expected}"
        return super().repr_failure(excinfo)

    def reportinfo(self):
        return self.path, self.lineno - 1, f"case: {self.name}"
```

Result: node ids `test_math.cases::add`, `test_math.cases::mul`; the
failure section is headed `case: mul` and reads `2*3 gave 6, expected 7`
(9.1 also puts that text on the `FAILED` summary line; 8.4 shows only
the node id there).

- Create nodes only with `Class.from_parent(parent, ...)`. *lab:*
  `pytest.File(path=..., parent=...)` failed collection with `Direct
  construction of _pytest.nodes.File has been deprecated, please use
  _pytest.nodes.File.from_parent`.
- Pass extra constructor arguments as keywords and forward `**kwargs`.
- `eval` is for the example only; never evaluate text from files you do
  not control.

## Removing and reordering items

```python
def pytest_collection_modifyitems(config, items):
    keep, drop = [], []
    for item in items:
        (drop if item.get_closest_marker("slow") else keep).append(item)
    if drop:
        config.hook.pytest_deselected(items=drop)   # counted as "deselected"
        items[:] = keep                             # change the list in place
```

*lab:* `collected 3 items / 1 deselected / 2 selected`. Assigning a new
list to `items` does nothing (*lab:* `items = [...]` in the hook, and all
3 tests still ran); change it in place.
