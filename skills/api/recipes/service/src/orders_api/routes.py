"""The /orders resource.

Contract (core/design.md):
  POST  /orders                  201 + Location; Idempotency-Key replays; 422
  GET   /orders?limit=&cursor=   200 {items, next_cursor}; newest first; 422
  GET   /orders/{id}             200 + ETag; 404
  PATCH /orders/{id}             merge patch; If-Match optional; 200 + ETag;
                                 404, 409 (cancelled or raced), 412, 422
  POST  /orders/{id}/cancel      200; repeat is a no-op; 404
"""

import hashlib
import json
from typing import Annotated, Any

from fastapi import APIRouter, Body, Header, HTTPException, Query, Response
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from orders_api import pages
from orders_api.deps import Now, StoreDep
from orders_api.models import CancelRequest, Order, OrderIn, OrderPage, OrderPatch
from orders_api.patching import apply_patch
from orders_api.store import Store

router = APIRouter(prefix="/orders", tags=["orders"])

WRITE_RETRIES = 3


def etag(order: dict[str, Any]) -> str:
    return f'"{order["revision"]}"'


def if_match_holds(if_match: str, current: str) -> bool:
    """RFC 9110 section 13.1.1: "*" or a list of tags, compared strongly."""
    if if_match.strip() == "*":
        return True                            # the resource exists: found() checked
    return current in (tag.strip() for tag in if_match.split(","))


def fingerprint(fields: dict[str, Any]) -> str:
    """Tells a true retry (same body) from a reused key (another body)."""
    return hashlib.sha256(json.dumps(fields, sort_keys=True, default=str).encode()).hexdigest()


def found(store: Store, order_id: int) -> dict[str, Any]:
    order = store.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return order


@router.post("", status_code=201)
def create_order(
    body: OrderIn,
    store: StoreDep,
    now: Now,
    response: Response,
    idempotency_key: Annotated[str | None, Header(max_length=200)] = None,
) -> Order:
    fields = body.model_dump()
    if idempotency_key is not None:
        seen = store.claim_key(idempotency_key, fingerprint(fields))
        if seen is not None:
            if seen["fingerprint"] != fingerprint(fields):
                raise HTTPException(422, "This Idempotency-Key was used with a different body")
            if seen["response"] is None:
                raise HTTPException(409, "A request with this Idempotency-Key is in progress")
            response.headers["Location"] = f"/orders/{seen['response']['id']}"
            return seen["response"]           # the first answer, not a second order
    try:
        order = store.insert(fields, created_at=now)
    except Exception:
        if idempotency_key is not None:
            store.release_key(idempotency_key)  # nothing was created: a retry may run
        raise
    if idempotency_key is not None:
        store.finish_key(idempotency_key, order)
    response.headers["Location"] = f"/orders/{order['id']}"
    return order


@router.get("")
def list_orders(
    store: StoreDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: Annotated[str | None, Query(max_length=200)] = None,
) -> OrderPage:
    after = pages.decode(cursor) if cursor else None
    rows = store.page(limit + 1, after)       # one extra row says whether more exist
    items, more = rows[:limit], len(rows) > limit
    last = items[-1] if items else None
    next_cursor = pages.encode(last["created_at"], last["id"]) if more and last else None
    return OrderPage(items=items, next_cursor=next_cursor)


@router.get("/{order_id}")
def get_order(order_id: int, store: StoreDep, response: Response) -> Order:
    order = found(store, order_id)
    response.headers["ETag"] = etag(order)
    return order


@router.patch("/{order_id}")
def patch_order(
    order_id: int,
    body: Annotated[
        dict[str, Any],
        Body(description="JSON merge patch of OrderIn: omitted fields stay, null clears."),
    ],
    store: StoreDep,
    response: Response,
    if_match: Annotated[str | None, Header()] = None,
) -> Order:
    # The body is a dict, not OrderPatch: FastAPI validates a model parameter
    # without the context={"partial": True} that apply_patch passes.
    for _ in range(WRITE_RETRIES):
        stored = found(store, order_id)
        if if_match is not None and not if_match_holds(if_match, etag(stored)):
            raise HTTPException(412, "The order changed since you read it; GET it again")
        if stored["status"] == "cancelled":
            raise HTTPException(409, "A cancelled order cannot be changed")
        try:
            result = apply_patch(Order.model_validate(stored), OrderPatch, body)
        except ValidationError as e:
            # raised inside the endpoint it would be a 500; make it the usual 422
            raise RequestValidationError(
                [{**err, "loc": ("body", *err["loc"])} for err in e.errors(include_url=False)]
            ) from e
        saved = store.update_if_revision(order_id, result.changes, stored["revision"])
        if saved is not None:
            response.headers["ETag"] = etag(saved)
            return saved
        # another write came between our read and our write: merge again
    raise HTTPException(409, "The order kept changing; try again")


@router.post("/{order_id}/cancel")
def cancel_order(order_id: int, body: CancelRequest, store: StoreDep,
                 response: Response) -> Order:
    for _ in range(WRITE_RETRIES):
        stored = found(store, order_id)
        if stored["status"] == "cancelled":
            response.headers["ETag"] = etag(stored)
            return stored                      # cancelling twice is not an error
        saved = store.update_if_revision(
            order_id, {"status": "cancelled", "cancel_reason": body.reason}, stored["revision"])
        if saved is not None:
            response.headers["ETag"] = etag(saved)
            return saved
    raise HTTPException(409, "The order kept changing; try again")
