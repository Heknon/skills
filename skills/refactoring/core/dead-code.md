# Dead code: the evidence before a delete

**Verdict you produce, per name:**

```
name:      <dotted name>, <public | private>
searched:  <patterns, all files> -> <hits other than the definition, or none>
reached:   <decorator registry | dispatch table | string in <file> | entry point | test only | none found>
not seen:  <what-search-misses items that apply and could not be ruled out>
decision:  <removed in <hash> | kept: <evidence> | kept, asked: <what would settle it>>
checks:    <after removal: tests, import_all with --config, probe>
```

Deleting is the one step that cannot be undone by the next reader: once
the code is gone, nothing points at the caller that needed it. A search
that finds no call proves only that no line spells a call.

## Steps

1. **Take one name at a time.** Locate its definition (navigation's
   `core/locate.md`) and note: public or private (leading underscore),
   decorated or not, in a module others import or not.
2. **Trace in** with navigation's `core/trace-in.md`, including step 6
   (can it be reached from outside), and search all files for the bare
   name (`git grep -n -w -I <name>`), not only calls.
3. **Go through `core/what-search-misses.md`** (navigation), item by
   item. The ones that kept code alive in the lab:

   | How it was reached | What showed it |
   | --- | --- |
   | `@handler("refund")` stored it in `HANDLERS`, and the queue consumer called `HANDLERS[kind](event)` | the decorator line above the definition; `HANDLERS\[` in `events/consumer.py` |
   | `config/routes.yaml` named `events.handlers.on_invoice`, loaded with `importlib` and `getattr` | the name found only in the YAML file; `tools/import_all.py events --config config/routes.yaml` |

   Removing `on_invoice` left the tests (1 passed), ruff and mypy all
   green; only `import_all.py --config config/routes.yaml` reported
   `FAIL config/routes.yaml: events.handlers.on_invoice AttributeError:
   module 'events.handlers' has no attribute 'on_invoice'`.
4. **Decide.**

   | Evidence | Decision |
   | --- | --- |
   | private, no hit but its definition, not decorated, none of the eleven items applies | remove |
   | any use found: registry, table, string, entry point, config | keep, and cite the use |
   | public, no use in this repository | keep and ask, or remove only if the person agreed; say which repositories and data were not searched |
   | used only by tests | keep; report "used only by tests" as a finding (navigation) |
   | reached by outside data (a message kind, a route, a setting) | keep: outside data can bring any key |

5. **Remove in its own commit**, one or a few names, with the searches
   in the body. Then the checks (`core/checks.md`), with `import_all.py
   --config` on every config file that names code. Search once more for
   the name: no hit left but explained ones.

## Tools that do not decide this

ruff, mypy and pyright do not report unused public functions: in the
lab none of them said anything about `on_ping`, a public handler that
nothing registered or routed. A dead-code finder, if the mirror has
one, gives leads, never a verdict: it cannot see strings, config or
other repositories either.

## Never

- Never delete on one search for `name(`.
- Never delete a public name because this repository does not call it,
  without saying what was not searched.
- Never delete in the same commit as a move or rename.
