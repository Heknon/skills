# Security pass

**Verdict you produce:** every outside input the change reads, traced
to where it is used, and findings each with the input that exploits it.

```
inputs:    POST /session body (dict[str, Any]) src/app/api.py:20
traced:    body["token"] -> find_session(token) src/app/api.py:24 -> find_one filter src/app/sessions.py:12
[1 blocker] src/app/api.py:20  SEC1  body {"user": "ann", "token": {"$ne": null}} -> ann's session without her token
searched:  SEC1 to SEC6 signs on the diff; route decorators and Depends in the changed files
verdict security: <findings: IDs | none found: <what was searched, and where>>
```

## Steps

1. **List the inputs the change reads**: route parameters, bodies,
   headers, cookies, query strings, uploaded files, queue messages,
   environment and files. In FastAPI the route signature says which
   is which (api: `fastapi/parameters.md`).
2. **Trace each input to where it is used** (navigation's Follow,
   `core/follow.md`): every hop as `path:line`, to a sink.
3. **Check each sink** against `checklists/security.md`: a query
   filter or update (SEC1), a response (SEC2), an authorisation check
   (SEC3), a shell, `eval`, a deserialiser or SQL text (SEC4), a path
   (SEC5), a log or an error message (SEC6), a size (SEC7).
4. **Write the exploiting input** for each finding, and run it when
   that is cheap and safe: against the test client with a local or fake
   store, never against a shared environment. *lab, MongoDB 8.0.32,
   PyMongo 4.18.2:* `find_one({"user": "ann", "token": {"$ne": None}})`
   and `{"$gt": ""}` in place of the token both returned ann's
   document. A test double that compares values only never shows this.
5. **Say what you searched** when nothing is found: `none found` names
   the inputs traced, the sinks checked and the files read. "No
   security issues" alone is not an answer.

## Never

- Never send an exploit to anything but a local run or a test client.
- Never paste a real secret found in the code into the answer: say
  where it is and that it must be rotated (git: `core/secrets.md`).
