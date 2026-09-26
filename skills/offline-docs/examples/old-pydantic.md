# Worked example: the installed version is not the one you remember

Kinds: Version, Signature. Verdict: confirmed from source. Commands and
output from a lab run of eval `old-pydantic` (Linux, uv 0.12.19, CPython
3.12.14); `.../site-packages` stands for
`/home/user/od-lab/ex1/.venv/lib/python3.12/site-packages`.

## The ask

> Fill in `patch_to_dict` in `app/patch.py`: it should turn an
> `OrderPatch` into a dict holding only the fields the client actually
> sent.

Memory says `patch.model_dump(exclude_unset=True)`. That is a lead for
what to look for, not the answer.

## Steps

1. **Pin** (`core/pin-version.md`):

   ```
   > uv run --no-sync python <skill>\recipes\lookup.py pin pydantic
   python:    3.12.14 at /home/user/od-lab/ex1/.venv/bin/python
   dist:      pydantic 1.10.26
   location:  .../site-packages
   installer: uv
   install:   a copy from an index (no direct_url.json)
   import:    pydantic -> .../site-packages/pydantic/__init__.cpython-312-x86_64-linux-gnu.so (compiled; its .py source is beside it)
   compiled:  25 file(s) in the package, such as env_settings.cpython-312-x86_64-linux-gnu.so
   typed:     pydantic ships py.typed
   ```

   pydantic 1, not 2. `model_dump` belongs to pydantic 2's API as
   remembered; check whether 1.10.26 has it.

2. **Look for both names** in the installed package (`core/discover.md`):

   ```
   > uv run --no-sync python <skill>\recipes\lookup.py grep pydantic "def (dict|model_dump)\b"
   .../site-packages/pydantic/main.py:450: def dict(
   1 match(es) for /def (dict|model_dump)\b/ in 53 file(s) under .../site-packages/pydantic and its METADATA
   ```

   No `model_dump` anywhere in 1.10.26. The same call confirms it:
   `AttributeError: 'OrderPatch' object has no attribute 'model_dump'`.

3. **Read the signature** (`core/signature.md`):

   ```
   > uv run --no-sync python <skill>\recipes\lookup.py def pydantic.BaseModel.dict
   imported:  pydantic (its top-level code ran)
   object:    _cython_3_2_3.cython_function_or_method
   signature: (self, *, include: ... = None, exclude: ... = None, by_alias: 'bool' = False, skip_defaults: 'Optional[bool]' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False) -> "'DictStrAny'"
   source:    none from inspect (TypeError); compiled from .../site-packages/pydantic/main.py:450
   module:    pydantic.main at .../site-packages/pydantic/main.cpython-312-x86_64-linux-gnu.so
   ```

   The method is compiled (Cython), so `inspect.getsource` fails; its
   code object names `main.py` line 450, the `.py` shipped beside the
   compiled module in the same wheel (`python/inspect.md`).

4. **Read the lines that decide "only the fields sent"**
   (`core/behaviour.md`), with `lookup.py lines <file> <start> <end>`:

   ```
   main.py:457          exclude_unset: bool = False,
   main.py:371          object_setattr(__pydantic_self__, '__fields_set__', fields_set)
   main.py:912          if exclude_unset:
   main.py:913              keys = self.__fields_set__.copy()
   ```

   `__init__` records the fields that were passed; `exclude_unset=True`
   keeps only those keys.

5. **Write it and run it**: `return patch.dict(exclude_unset=True)`.

   ```
   > uv run --no-sync python -c "from app.models import OrderPatch; from app.patch import patch_to_dict; print(patch_to_dict(OrderPatch(status='paid'))); print(patch_to_dict(OrderPatch(note=None, quantity=3))); print(patch_to_dict(OrderPatch()))"
   {'status': 'paid'}
   {'note': None, 'quantity': 3}
   {}
   ```

   A field sent as `None` is kept, one not sent is left out: what a
   PATCH needs.

## The answer

```
## Answer
Answer:   pydantic 1.10.26 is installed, which has no model_dump. Use
          patch.dict(exclude_unset=True); app/patch.py now does.
Checked:  pydantic 1.10.26, Python 3.12.14, /home/user/od-lab/ex1/.venv/bin/python
Evidence: pydantic/main.py:450 def dict(..., exclude_unset: bool = False, ...);
          main.py:912-913 keeps only __fields_set__ when exclude_unset;
          run: OrderPatch(status='paid') -> {'status': 'paid'},
          OrderPatch(note=None, quantity=3) -> {'note': None, 'quantity': 3}
Source:   code
Verdict:  confirmed from source at .../site-packages/pydantic/main.py:450 on pydantic 1.10.26

## Not checked
- Other pydantic versions: not installed, not checked. After an upgrade,
  look this up again.
- The Windows build (main.cp312-win_amd64.pyd, same main.py); not run on Windows.
```
