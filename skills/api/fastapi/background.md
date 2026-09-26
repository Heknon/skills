# Background tasks

`BackgroundTasks` runs small functions after the response is sent, in
the same process. It is not a queue.

```python
@router.post("/orders/{order_id}/receipt")
def send_receipt(order_id: int, tasks: BackgroundTasks) -> dict:
    tasks.add_task(email_receipt, order_id)     # a def runs in the threadpool
    return {"queued": True}
```

## When they run (*lab*, FastAPI 0.141.1 and 0.118.0)

- **After the response is sent.** Under uvicorn, an endpoint that added
  a task sleeping 2 s answered in 0.00 s.
- **In order**, one after another: `background one`, `background two`.
- **Inside TestClient, before the call returns**: the test sees their
  effects right after `client.get(...)`, which hides how late they run
  in production.

## When one fails (*lab*)

- The client already has its 200; it never learns.
- The **remaining tasks do not run**: `bg_fail` raised and the task
  added after it never ran.
- TestClient with the default `raise_server_exceptions=True` raises the
  task's exception (`RuntimeError: bg failed`) from the request call;
  with `False`, the test sees 200.

## What that means

| Need | Use |
| --- | --- |
| a log line, a cache refresh, a best-effort notification | `BackgroundTasks` |
| work that must happen (an email the customer paid for, a ledger entry) | a durable queue or an outbox table written in the same transaction as the change; not this skill's ground |
| work longer than the shutdown grace period | not `BackgroundTasks`: a deploy or scale-down kills it midway (deployment skill) |

## Background tasks and yield dependencies

*lab:* with a default-scope yield dependency (a session) and a
background task in one request, 0.141.1 and 0.118.0 logged `session
open, background task runs, session closed`: the session was still open
while the task ran. 0.117.1 logged `session open, session closed,
background task runs`. A task that uses a request's session therefore
works on one version and fails on the other, and keeps a connection busy
for as long as the task runs. Pass the task ids and values, and let it
open what it needs (`fastapi/dependencies.md`, scope).
