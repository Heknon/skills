# Security

Run for any change a request, a message or a file from outside can
reach, and in full for the Security kind (`core/security-pass.md`).
Every finding names the input that exploits it.

### SEC1 Request data reaches a MongoDB query as a dict

- **Ask:** can a client send an object where the code expects a string?
  A body typed `dict`, `dict[str, Any]`, `Any`, `Body()` of a dict,
  `await request.json()` or `json.loads(...)` passes objects through,
  and `{"$ne": null}` in a filter matches every document.
- **Scenario (lab, MongoDB 8.0.32, PyMongo 4.18.2):**
  `find_one({"user": "ann", "token": {"$ne": None}})` returned ann's
  document, and so did `{"$gt": ""}` as the token. A pydantic model with
  `token: str` refused `{"$ne": null}` with `string_type` (pydantic
  2.13.5), so the same request would get a 422.
- **Severity:** blocker.
- **Fix to suggest:** a model with `str` fields (both spellings as two
  optional fields, or an alias), not a hand-written check.

### SEC2 A secret or hidden field reaches the client

- **Ask:** does any response carry a password hash, token, key, an
  internal flag or another user's data?
- **Scenario:** a route that returns the stored document, not a
  response model, sends every stored field, the password hash included.
- **Severity:** blocker.
- **Facts:** architecture (L3, a database model at the boundary) and
  api (`core/review.md`: response declared).

### SEC3 Nobody checks who may do this

- **Ask:** for a route that reads or changes a resource by id, where is
  it checked that the caller may? A new route next to guarded ones
  without the same dependency is the common case.
- **Severity:** blocker when another user's data can be read or changed.

### SEC4 Code or query built from input

- **Ask:** does input reach `subprocess` with `shell=True`,
  `os.system`, `eval`, `exec`, `pickle.loads`, `yaml.load`, or an SQL
  string built with an f-string or `+`?
- **Severity:** blocker.

### SEC5 A path built from input

- **Ask:** can `..`, an absolute path or a drive letter in a name reach
  `open`, `Path`, `FileResponse` or a delete?
- **Severity:** blocker when it reads or writes outside the folder.

### SEC6 A secret in the code, the log or the error

- **Ask:** is a key, token or password written as a literal, logged, or
  put into an exception message that reaches a client or a log?
- **Severity:** blocker for a real secret in the repository; the git
  skill's `core/secrets.md` says what to do about one already
  committed.

### SEC7 Input without a limit

- **Ask:** is every string, list and page size from outside bounded?
- **Facts:** api (`core/review.md`, "inputs bounded").

## Signs

```
SEC1  +  :\s*(dict|Dict|Any)(\[[^\]]*\])?\s*(=\s*Body\([^)]*\))?\s*[,)]|:\s*(dict|Dict|Any)(\[[^\]]*\])?\s*$|request\.json\(\)|json\.loads\(|["']\$(where|function|accumulator)["']
SEC2  +  ^\s+\w*(password|passwd|hash|token|secret)\w*\s*[:=]|["']\w*(password|passwd|hash|token|secret)\w*["']\s*:
SEC3  +  @\w+\.(get|post|put|patch|delete)\(\s*["'][^"']*\{\w*id\w*\}
SEC4  +  shell\s*=\s*True|os\.system\(|\beval\(|\bexec\(|pickle\.loads?\(|yaml\.load\(|execute\(\s*f["']|text\(\s*f["']
SEC5  +  FileResponse\(|send_file\(|open\(.*\b(name|path|filename)\b
SEC6  +  (api_key|secret|token|password)\s*=\s*["'][^"']+["']|log\w*\.(debug|info|warning|error|exception)\(.*(password|token|secret|api_key)
```
