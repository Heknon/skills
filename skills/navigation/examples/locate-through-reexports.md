# Worked example: Locate through re-exports and an alias

Follow this for a "where is X defined" question. Copy the order of the
steps and the answer shape; change the names.

## The ask

> Where is the `Client` class defined? `orders/sync.py` uses it.

## Steps

1. **Start from the user of the name** (`core/locate.md` step 1). Read the
   imports of `orders/sync.py`:

   ```
   orders/sync.py:3: from shop import Client
   ```

2. **Turn the import into a file** (`python/imports.md`): `from shop import
   Client` looks first for the name `Client` in `shop/__init__.py`.

   ```
   shop/__init__.py:1: from .api import Client
   ```

   An import, not a definition: a re-export. Follow it.

3. `from .api import Client` inside package `shop` means the name `Client`
   in `shop/api/__init__.py`:

   ```
   shop/api/__init__.py:2: from ._http import HttpClient as Client
   ```

   Another re-export, and a rename: the class is called `HttpClient`
   where it is defined.

4. `from ._http import HttpClient` means `shop/api/_http.py`. Search it
   with a definition pattern for the real name:

   ```
   grep ^\s*class\s+HttpClient\b in shop/api/_http.py
   shop/api/_http.py:12: class HttpClient:
   ```

5. **A search for `class Client` would have found this instead**:

   ```
   legacy/client.py:8: class Client:
   ```

   A different class that `orders/sync.py` never reaches. This is why the
   chain starts from the using file.

6. **Confirm with the interpreter** (`tools/terminal-probes.md`):

   ```
   > .venv\Scripts\python.exe -c "import inspect, shop; print(inspect.getsourcefile(shop.Client), inspect.getsourcelines(shop.Client)[1])"
   C:\work\shop-app\shop\api\_http.py 12
   ```

## The answer

```
## Found
shop/api/_http.py:12 - class HttpClient, which orders/sync.py uses under the name Client

## How I know
orders/sync.py:3 imports Client from shop.
shop/__init__.py:1 re-exports it from .api.
shop/api/__init__.py:2 re-exports HttpClient from ._http under the name Client.
shop/api/_http.py:12 defines class HttpClient.
The interpreter confirms: inspect.getsourcefile(shop.Client) is shop\api\_http.py, line 12.
A second class named Client exists at legacy/client.py:8; orders/sync.py does not reach it.

## Not covered
none
```
