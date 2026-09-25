# pluggy

pluggy is the plugin library under pytest (1.6.0 with both pytest 8.4.2
and 9.1.1 in the lab). It knows nothing about tests: it holds hook
specifications and implementations and calls them.

| pluggy | In pytest |
| --- | --- |
| `PluginManager` | `config.pluginmanager` (a `PytestPluginManager`) |
| `HookspecMarker("pytest")` | `pytest.hookspec` |
| `HookimplMarker("pytest")` | `pytest.hookimpl` |
| `pm.hook.<name>(**kwargs)` | `config.hook.<name>(...)`, `item.ihook.<name>(...)` (filtered to the conftests that apply to the item) |
| `pm.register(obj, name)` | `config.pluginmanager.register(obj, "name")` |
| `pm.get_plugin(name)`, `pm.has_plugin(name)`, `pm.list_name_plugin()` | `config.pluginmanager.get_plugin("name")`, `hasplugin("name")` |
| `pm.hook.<name>.get_hookimpls()` | the implementations, in reverse call order (*lab:* call order `first, b, a, last`, list `last, a, b, first`) |
| `pm.add_hookcall_monitoring(before, after)` | used by pytester's hook recorder |

## How a hook call runs (`pluggy/_callers.py`, `_multicall`)

*lab*, a pure pluggy script with seven plugins:

```
registered: first(1), second(2), trylast(3), tryfirst(4), returns_none(None),
            new-style wrapper W, old-style wrapper OldW (registered last)
call order: OldW before, W before, tryfirst, returns_none, second, first,
            trylast, W after, OldW after
result:     [4, 2, 1, 3, 'added-by-wrapper']     (None dropped; W appended)
firstresult hook: only tryfirst ran; result 4
```

- Non-wrappers: `tryfirst` ones, then the rest last-registered first, then
  `trylast` ones.
- Wrappers wrap everything, last-registered outermost.
- `None` results are left out of the list; a firstresult hook stops at
  the first non-`None`.
- An exception in an implementation stops the other implementations and
  is raised into each wrapper at its `yield`; a new-style wrapper can
  catch it and return a result instead (*lab:* `['recovered from boom']`);
  an old-style wrapper sees it in `outcome.exception`, and it propagates
  unless the wrapper calls `outcome.force_result(...)`.
- Historic hooks: `pm.hook.x.call_historic(kwargs={...})` is remembered;
  a plugin registered later has its implementation called immediately
  (*lab:* `late plugin got historic call x = 1`).
- Calls take keyword arguments only (*lab:* `HookCaller.__call__() takes
  1 positional argument but 2 were given`).

## Validation

At registration pluggy checks each `pytest_*` function against its
specification: extra argument names are an error. Names without a
specification are checked when pytest calls `check_pending()`, after
collection and before `pytest_collection_modifyitems` (`_pytest/main.py`):
unknown names are an error unless `optionalhook=True`, so conftests
found during collection are checked too.
