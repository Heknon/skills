# Signature: what a function accepts and returns

**Verdict you produce:** the parameters as the installed code defines
them, the `def` line as `path:line`, and, for `*args` or `**kwargs`,
where those arguments land.

```
signature: <name>(<parameters>) -> <return, if annotated>
def:       <path>:<line>
kwargs:    <passed to <function> at <path>:<line>, which accepts <names> | none>
```

Pin the version first (`core/pin-version.md`).

## Steps

1. **Ask the interpreter** (this imports the module; read
   `python/pydoc.md` "Imports run code" first if you do not know it):

   ```powershell
   uv run --no-sync python <skill>\recipes\lookup.py def fetchkit.get
   ```

   ```
   imported:  fetchkit (its top-level code ran)
   object:    builtins.function
   signature: (url, **kw)
   source:    /home/user/od-lab/vendored-copy/.venv/lib/python3.12/site-packages/fetchkit/__init__.py:9
   module:    fetchkit at /home/user/od-lab/vendored-copy/.venv/lib/python3.12/site-packages/fetchkit/__init__.py
   doc:       Fetch url.
   ```

   Without the recipe:
   `uv run --no-sync python -c "import inspect, fetchkit as m; print(inspect.signature(m.get)); print(inspect.getsourcefile(m.get), inspect.getsourcelines(m.get)[1])"`.

2. **Read the `def`** at that line (`recipes/lookup.py lines <path> <n>`,
   or the editor's `read_file` when the path is inside the project).
   Defaults, `*` (keyword-only after it) and `/` (positional-only
   before it) are read from there.

3. **Follow `*args` and `**kwargs`.** A signature with `**kwargs` does not
   accept anything; it passes the arguments on. Find the call that
   receives them in the body and repeat steps 1 and 2 for that function,
   until you reach a function with named parameters:

   ```
   fetchkit/__init__.py:14      return _send("GET", url, **kw)
   fetchkit/_transport.py:7     def _send(method, url, *, body=None, query=None, headers=None, timeout=None):
   ```

   So `fetchkit.get` 2.0.0 accepts `body`, `query`, `headers` and
   `timeout`, and nothing else: `get(url, verify=False)` raised
   `TypeError: _send() got an unexpected keyword argument 'verify'`
   (*lab*, eval `kwargs-passthrough`). The error names the inner
   function, not the one you called.

   A real one: requests 2.34.2, `requests.get(url, params=None, **kwargs)`
   (`requests/api.py:74`) calls `request("get", url, params=params,
   **kwargs)` (line 87), which calls `session.request(method=method,
   url=url, **kwargs)` (line 71); `Session.request` at
   `requests/sessions.py:557` names `verify`, `timeout`, `cert` and the
   rest (*lab*).

4. **Decorated functions**: see "Wrappers" below before trusting the
   signature.

5. **No signature, no source** (a compiled function): `python/inspect.md`
   says which fail; read a stub (`python/stubs.md`) or the docstring, and
   the verdict becomes "confirmed from stub only" or "from help only".

## Wrappers

`inspect.signature` follows `__wrapped__`, which `functools.wraps` sets.
It then reports the wrapped function's parameters, not the wrapper's.
Recorded on 3.12.14 with three decorators:

| Decorator | `signature(f)` | `signature(f, follow_wrapped=False)` | True call |
| --- | --- | --- | --- |
| `@logged`, `wraps`, passes all arguments on | `(amount, *, currency='EUR')` | `(*args, **kwargs)` | as shown |
| `@with_session`, `wraps`, supplies the first argument itself | `(session, user_id, *, active=True)` | `(*args, **kwargs)` | `load_user(7)`; `load_user('S', 7)` raised `TypeError: load_user() takes 2 positional arguments but 3 were given` |
| `@plain`, no `wraps` | `(*args, **kwargs)`, and `__name__` is `wrapper` | the same | hidden: read the decorated `def` |

So when `hasattr(f, '__wrapped__')` (the recipe prints a `wrapper:`
line), read the wrapper's body too: it may add, remove or fill in
arguments. `inspect.getsourcelines` also follows `__wrapped__`, and
returns the line of the first decorator above the `def` (*lab*: line 24
was `@logged`, the `def` was line 25).

## Report

The signature as printed, the `def` line, each `**kwargs` hop as
`path:line`, and the verdict. If the answer is "that keyword does not
exist", the verdict is `not found (...)` with each function you followed
(`core/evidence.md`).

## Never

- Never answer "`**kwargs` accepts anything". Follow it, or say you could
  not and why.
- Never pass a keyword to see what happens in code that may reach the
  network or change data; read the receiving `def` instead. A call that
  only builds values, as in the lab, is fine.
- Never report `(*args, **kwargs)` as the answer; that is a wrapper's
  signature.
