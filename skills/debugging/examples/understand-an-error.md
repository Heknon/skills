# Worked example: a JSON error that was a gateway page

Kinds: Read, Understand. Copy the order of the steps and the verdict's
shape. Outputs are from a lab run on Python 3.12.14 and httpx 0.28.1: a
small client, `rates`, calling a local server that stands in for a
proxy whose upstream is down (it answers every request with a 502 HTML
page).

## The ask

> `uv run python -m rates` fails with JSONDecodeError. Is the rates
> service sending bad JSON?

## Steps

1. **Run it and read the whole traceback** (`core/read-traceback.md`):

   ```
   $ uv run python -m rates
   Traceback (most recent call last):
     File "<frozen runpy>", line 198, in _run_module_as_main
     File "<frozen runpy>", line 88, in _run_code
     File "/root/dbg-lab/understand/rates/__main__.py", line 3, in <module>
       print(get_rates("http://127.0.0.1:8765")["EUR"])
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
     File "/root/dbg-lab/understand/rates/client.py", line 6, in get_rates
       return response.json()["rates"]
              ^^^^^^^^^^^^^^^
     File "/root/dbg-lab/libs/.venv/lib/python3.12/site-packages/httpx/_models.py", line 832, in json
       return jsonlib.loads(self.content, **kwargs)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
     File "/root/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu/lib/python3.12/json/__init__.py", line 346, in loads
       return _default_decoder.decode(s)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^
     File "/root/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu/lib/python3.12/json/decoder.py", line 338, in decode
       obj, end = self.raw_decode(s, idx=_w(s, 0).end())
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
     File "/root/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu/lib/python3.12/json/decoder.py", line 356, in raw_decode
       raise JSONDecodeError("Expecting value", s, err.value) from None
   json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
   ```

   One block. The raising frame is in the standard library; the deepest
   project frame is `client.py` line 6, `response.json()`.
2. **Split the last line** (`core/understand-error.md`, step 1): the
   type is `json.decoder.JSONDecodeError`, the standard library's, raised
   through httpx. The message: `Expecting value` at character 0.
3. **Look up the type** (`python/exceptions.md`): the text is not JSON.
   Under *Messages that hide the cause*: an empty body and an HTML page
   both print exactly this. The message cannot tell them apart, and
   says nothing about the service.
4. **Print the value behind it**: the response, status first, where
   `client.py` used it:

   ```
   $ uv run python -c "import httpx; r = httpx.get('http://127.0.0.1:8765/v1/rates', timeout=5); print(r.status_code, r.headers.get('content-type'), repr(r.text[:80]))"
   502 text/html '<html><head><title>502 Bad Gateway</title></head><body>502 Bad Gateway</body></h'
   ```

   Without a network call, the exception holds the same text:
   `exc.doc` was `'<html><head><title>502 Bad Gat'` in its first 30
   characters (*lab*).
5. **Where it came from**: the body is a gateway's error page, not the
   rates service's JSON. What a 502 means is api's
   (`core/methods-and-status.md`); here, the proxy could not reach the
   service.

## The verdict

```
error:     json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
whose:     standard library, raised through httpx's Response.json()
means:     the body is not JSON; an empty body or an HTML page print exactly this
value:     502 text/html '<html><head><title>502 Bad Gateway</title>...'
came from: the gateway in front of the rates service, which could not reach it
shown by:  the probe in step 4
owner:     this skill for the code; the service's owners for the 502 (api for what it means)
```

The rates service did not send bad JSON; it was not reached. The code
has a bug of its own: `client.py` reads the body without checking the
status. With `response.raise_for_status()` before `.json()` the same
run says what happened (*lab*):

```
httpx.HTTPStatusError: Server error '502 Bad Gateway' for url 'http://127.0.0.1:8765/v1/rates'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/502
```

That line changes what `get_rates` raises, so it goes through
`core/improve-the-error.md`: first search for callers that catch
`JSONDecodeError` or `ValueError` (its base), and check the URL it
prints carries no token (`HTTPStatusError` prints the query string,
`python/exceptions.md`, *Library errors*).
