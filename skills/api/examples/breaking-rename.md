# Worked example: a "small cleanup" that would have broken clients

Kinds: Evolve, Review. Outputs from a lab run on FastAPI 0.141.1 and
pydantic 2.13.5 (the eval sandbox rename-field).

## The ask

> Small cleanup: rename qty to quantity in the lines API and make note
> required. No need for a new version.

## Steps

1. **Class each change** (`core/compatibility.md`):
   - renaming `qty`: rules 4 and 5, **breaking**: old clients send
     `qty` (now an unknown key) and read `qty` (now missing).
   - requiring `note`: rule 6, **breaking**: old clients omit it and get
     422.
2. **Who breaks.** `CLIENTS.md` lists the mobile app ("old versions
   stay installed for months") and the scanner firmware ("updated twice
   a year"). Neither can be moved in step with the server.
3. **The additive path instead**, and one question to the person
   about `note` (below). Dump the contract first:
   ```
   uv run --no-sync python <skill>/recipes/tools/openapi_dump.py shop.main:app before.json
   ```
   `wrote before.json: OpenAPI 3.1.0, 2 paths, 2 operations`
4. **Change the models.** Input accepts `quantity` or `qty` (both
   optional in the schema, one required by a model validator, 422 when
   they differ); output returns both; `qty` is marked deprecated in the
   schema only:
   ```python
   QTY_DEPRECATED = {"description": "Deprecated: use quantity.", "json_schema_extra": {"deprecated": True}}

   class LineIn(BaseModel):
       sku: str
       quantity: int | None = Field(default=None, ge=1)
       qty: int | None = Field(default=None, ge=1, **QTY_DEPRECATED)
       note: str | None = None
       # model_validator one_quantity: at least one, and equal if both

   class Line(BaseModel):
       id: int
       sku: str
       quantity: int = Field(ge=1)
       qty: int = Field(ge=1, **QTY_DEPRECATED)
       note: str | None = None
   ```
5. **Diff the contract**:
   ```
   uv run --no-sync python <skill>/recipes/tools/openapi_dump.py shop.main:app after.json
   git diff --no-index before.json after.json
   ```
   The first diff showed `-            "minimum": 1.0,` under the
   response's `qty`: the new `Line.qty` had lost `ge=1`, so the contract
   no longer promised a positive quantity. Put back (`Field(ge=1, ...)`
   on both output fields) and dumped again. The second diff, read line
   by line:
   - `Line`: `+ "quantity"` property; `qty` gains `"deprecated": true`;
     `required` reordered (`- "qty"` and `+ "qty"` are the same entry
     moving) plus `+ "quantity"`: a new field clients may ignore (rule 3).
   - `LineIn`: `+ "quantity"`; `qty` becomes `anyOf integer, null` with
     `"deprecated": true`; `required` loses `"qty"`: loosening (rule 8).
   - `version` `1.4.0` to `1.5.0`.
   No property removed, nothing newly required on input.
6. **Tests**: the existing `test_add_line` (sends `qty`, reads `qty`)
   unchanged and passing, plus `quantity` alone, and both-disagree or
   neither giving 422: `3 passed in 0.30s`.

## The answer

```
## Result
Both requested changes are breaking for clients in CLIENTS.md (old
mobile versions and the scanner firmware), so neither was shipped as
asked. Done instead, additively, in src/shop/main.py:
- quantity added; requests may send quantity or the old qty (422 if
  both differ or neither is sent); responses carry both; qty is marked
  deprecated in the OpenAPI document. Remove qty in a v2, or after logs
  show no client sends it.
- note left optional. Requiring it breaks every client that omits it.
  Question: should the server default it, or should a v2 require it?
  I recommend a server default until the scanner firmware is updated.

## Checked
- OpenAPI diff before/after: quantity added, qty deprecated, no field
  removed, qty no longer required on input (a loosening). The first
  diff caught a lost minimum on the response's qty; fixed.
- uv run pytest -q: 3 passed, the old test unchanged.
- FastAPI 0.141.1, pydantic 2.13.5.

## Not checked
- What the mobile and scanner clients do with the extra quantity field
  in responses; assumed ignored (rule 3), not confirmed with their code.
```
