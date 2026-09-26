# The OpenAPI document, offline

FastAPI builds an OpenAPI 3.1.0 document from the routes (*lab:*
`"openapi": "3.1.0"` on 0.141.1 and 0.118.0). It is the contract as
FastAPI understood it: the first thing to read when a parameter lands in
the wrong place, and the thing to diff when the contract changes.

## Why /docs is blank

The Swagger UI page at `/docs` is a small HTML shell that loads
Swagger UI from a CDN. *lab,* `GET /docs` on 0.141.1 referenced:

```
https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css
https://fastapi.tiangolo.com/img/favicon.png
https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js
```

(the defaults of `swagger_js_url`, `swagger_css_url` and
`swagger_favicon_url` in `fastapi/openapi/docs.py`; `/redoc` loads
`https://cdn.jsdelivr.net/npm/redoc@2/bundles/redoc.standalone.js`). Air
gapped, the scripts do not load and the page stays empty. The app is
fine; `/openapi.json` still answers (*lab:* 200 `application/json`).
Nothing in the app needs fixing.

Options, in order:

1. **Read the document itself**: `GET /openapi.json`, or dump it without
   a server (below).
2. **Serve Swagger UI from assets the team hosts internally**, if a
   person can provide `swagger-ui-bundle.js` and `swagger-ui.css` on an
   internal URL:

   ```python
   from fastapi.openapi.docs import get_swagger_ui_html

   app = FastAPI(docs_url=None)                  # turn off the CDN page

   @app.get("/docs", include_in_schema=False)
   def docs():
       return get_swagger_ui_html(
           openapi_url=app.openapi_url, title="Orders API",
           swagger_js_url="https://assets.example.internal/swagger-ui/swagger-ui-bundle.js",
           swagger_css_url="https://assets.example.internal/swagger-ui/swagger-ui.css",
       )
   ```

   (*lab:* `get_swagger_ui_html` takes `openapi_url`, `title`,
   `swagger_js_url`, `swagger_css_url`, `swagger_favicon_url`,
   `oauth2_redirect_url`, `init_oauth`, `swagger_ui_parameters`.) The
   URLs are placeholders: never download the files from the internet
   yourself, and never add a package to get them.

## Dump it without a server

```
uv run --no-sync python <skill>/recipes/tools/openapi_dump.py orders_api.main:app openapi.json
```

*lab:* `wrote openapi.json: OpenAPI 3.1.0, 4 paths, 6 operations`. The
script imports the app (module-level code runs, the lifespan does not),
calls `app.openapi()`, and writes sorted, indented UTF-8 JSON itself, so
the output does not depend on how the shell redirects.

## Read an operation

```json
"/orders/{order_id}/cancel": {"post": {
  "operationId": "cancel_order_orders__order_id__cancel_post",
  "parameters": [{"in": "path", "name": "order_id", "required": true, ...}],
  "requestBody": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/CancelRequest"}}}, "required": true},
  "responses": {"200": {...}, "422": {...}}}}
```

| Look at | Tells you |
| --- | --- |
| `parameters[].in` | where each non-body input is read: `path`, `query`, `header`, `cookie` |
| `requestBody` | there is a body, and its schema; absent means none |
| `responses."200".content...schema` | the response model; `{}` means none declared (`fastapi/responses.md`) |
| `components.schemas.X.required` | which fields a client must send (inputs) or can rely on (outputs) |
| `"deprecated": true` | on an operation or a property: going away (`core/compatibility.md`) |

A model used as both body and response can appear twice, as
`Item-Input` and `Item-Output`. *lab:* a model with a computed field was
split (and stayed split with `separate_input_output_schemas=False`); a
plain model with a defaulted list stayed one `Item`. Diff both when
comparing versions.

## Diff two versions

Dump before you change the code, again after, then compare:

```
uv run --no-sync python <skill>/recipes/tools/openapi_dump.py shop.main:app before.json
# ... change the code ...
uv run --no-sync python <skill>/recipes/tools/openapi_dump.py shop.main:app after.json
git diff --no-index before.json after.json
```

For a change already made, dump the old commit from a separate
checkout, never by discarding the working tree (the git skill owns
checkouts and worktrees). Delete the two files afterwards; they are not
part of the change.

Read every `-` line against `core/compatibility.md`: a removed property
or path, a name added to a `required` list, a changed `type`, `enum`,
`maximum`, `maxLength` or `pattern`. *lab,* sandbox rename-field, the
additive rename: `+ "quantity"` in both schemas, `+ "deprecated": true`
on `qty`, and `- "qty"` only inside the request's `required` list (a
loosening). The breaking version would show `- "qty"` as a property.
