# Worked example: fix a shape change, then improve its error

Kinds: Fix, Understand, Improve. Copy the order of the steps and the
two commits. Outputs are from a lab run on Python 3.12.14, pytest 9.1.1
and git 2.43.0, in a copy of the `shape-change` sandbox (evals
`read-past-the-message` and `improve-in-own-commit`).

## The ask

> `uv run python -m stock data/feed-2026-09.json` fails with KeyError:
> 'price'. The August feed works. Fix it, and make sure the next person
> gets something clearer than KeyError: 'price'. Commit your work.

## Steps

1. **Reproduce** (`core/reproduce.md`): August prints `3 items, stock
   value 66.00`; September ends in

   ```
     File "/root/dbg-lab/runs/shape1/stock/report.py", line 3, in line_value
       return item["price"] * item["qty"]
              ~~~~^^^^^^^^^
   KeyError: 'price'
   ```

2. **Understand it** (`core/understand-error.md`). A built-in
   `KeyError`: the dict has no key `'price'`. The message names what was
   asked for, so print what was there, the whole item, at the deepest
   project frame (a probe, removed after):

   ```
   DBG item ['pricing', 'quantity', 'sku'] {'sku': 'A1', 'quantity': 4, 'pricing': {'unit': 4.5, 'currency': 'EUR'}}
   ```

   Two fields changed, not one, and the file says `"version": 2`. The
   value came from `stock/feed.py`, which passes the items through
   as they are. Tried on a copy: `item.get("price", 0)` and
   `item["pricing"]["unit"]` in `report.py` both ended in
   `KeyError: 'qty'`.
3. **Fix at the boundary, prove it, commit it** (`core/prove-the-fix.md`).
   `feed.py` turns a version 2 item into the shape the report reads:

   ```python
   def _from_version_2(item):
       """Version 2 feeds renamed qty and moved the price into "pricing"."""
       return {"sku": item["sku"], "qty": item["quantity"], "price": item["pricing"]["unit"]}
   ```

   ```
   $ uv run python -m stock data/feed-2026-09.json
   3 items, stock value 50.00
   $ uv run pytest -q
   3 passed in 0.01s
   $ git stash push -- stock/feed.py
   $ uv run python -m stock data/feed-2026-09.json
   KeyError: 'price'
   $ uv run pytest -q
   1 failed, 2 passed in 0.01s
   $ git stash pop
   $ git add -A && git commit -m "Read version 2 supplier feeds"
   ```

4. **Judge the error** (`core/improve-the-error.md`, step 1): `KeyError:
   'price'` named neither the file, nor the version, nor the keys that
   were there. Improve. The next change of shape shows how it would look
   today; two small inputs, outside the project:

   ```
   $ uv run python -m stock ../feed-v3.json
   KeyError: 'qty'
   $ uv run python -m stock ../feed-v2-bad.json
   KeyError: 'pricing'
   ```

5. **Where it entered, and who catches it**: `load_items` in `feed.py`.
   Nothing catches it:

   ```
   $ grep -rn "except" stock tests --include=*.py
   $ echo $?
   1
   ```

   So a built-in `ValueError` for an unknown version is safe
   (architecture's `placement/custom-errors.md`: no caller handles it
   differently). For an item missing a field, the `KeyError` stays and
   gains a note. Neither message carries more than a file name, a
   version number and key names.
6. **The change**, in `feed.py`:

   ```python
   KNOWN_VERSIONS = (1, 2)
   ...
       version = feed.get("version", 1)
       if version not in KNOWN_VERSIONS:
           raise ValueError(f"{path}: feed version {version!r} is not supported (known: 1, 2)")
       if version == 1:
           return feed["items"]
       items = []
       for number, item in enumerate(feed["items"], start=1):
           try:
               items.append(_from_version_2(item))
           except KeyError as exc:
               exc.add_note(f"{path}: item {number} of a version 2 feed has keys {sorted(item)}")
               raise
       return items
   ```

7. **Rerun**: the new text shows, and the fix still holds:

   ```
   $ uv run python -m stock ../feed-v3.json
   ValueError: ../feed-v3.json: feed version 3 is not supported (known: 1, 2)
   $ uv run python -m stock ../feed-v2-bad.json
   KeyError: 'pricing'
   ../feed-v2-bad.json: item 2 of a version 2 feed has keys ['price', 'quantity', 'sku']
   $ uv run python -m stock data/feed-2026-09.json
   3 items, stock value 50.00
   ```

8. **Test the type and the value**, not the sentence:

   ```python
   def test_unknown_feed_version_is_named(tmp_path):
       feed = tmp_path / "feed.json"
       feed.write_text('{"version": 3, "items": []}', encoding="utf-8")
       with pytest.raises(ValueError, match="feed version 3"):
           load_items(feed)
   ```

   `4 passed`; with `feed.py` from the fix commit, `Failed: DID NOT
   RAISE ValueError`.
9. **Its own commit**:

   ```
   $ git add -A && git commit -m "Name the feed version and item when a feed cannot be read"
   $ git log --oneline
   520ad10 Name the feed version and item when a feed cannot be read
   f998959 Read version 2 supplier feeds
   1a186e7 Add the stock value report
   ```

## Why two commits

In a copy, the two were squashed into one commit, then that commit was
reverted, as someone backing out a noisy message would:

```
$ git revert --no-edit HEAD
$ uv run python -m stock data/feed-2026-09.json
KeyError: 'price'
```

The bug came back. With the two commits, reverting the improvement
alone left `3 items, stock value 50.00`.

## The answer

```
## Cause
Supplier feeds changed to version 2 in September: "qty" became
"quantity" and "price" moved to "pricing"."unit". stock/feed.py passed
items through unchanged, so report.py:3 found no 'price' key.

## Reproduction
uv run python -m stock data/feed-2026-09.json -> exit 1, KeyError: 'price'.

## Fix
f998959 Read version 2 supplier feeds: stock/feed.py maps a version 2
item to the fields the report reads; test_september_feed_version_2.
Then 520ad10 Name the feed version and item when a feed cannot be read:
an unknown version raises ValueError naming the file and version; a
version 2 item missing a field keeps its KeyError with a note naming the
item and its keys; test_unknown_feed_version_is_named.

## Proof
With the fix: 3 items, stock value 50.00; 3 passed. With feed.py
stashed: KeyError: 'price'; 1 failed, 2 passed. Restored: 3 passed.
The improvement: a version 3 feed printed KeyError: 'qty' before and
ValueError: ../feed-v3.json: feed version 3 is not supported (known:
1, 2) after; its test fails without it. 4 passed.
```
