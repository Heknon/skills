"""An in-memory store, so the recipe runs anywhere.

It stands in for a database and shows only what the API needs from one:
a revision on every record, a write filtered on that revision, a keyset
read in a stable order, and a place to keep idempotency records. How a
real database does each is the mongodb skill's ground (a dotted $set
filtered on the revision, a keyset query and its index); where this code
lives in a layered service is the architecture skill's.
"""

import threading
from copy import deepcopy
from datetime import datetime
from typing import Any


class Store:
    def __init__(self) -> None:
        self._orders: dict[int, dict[str, Any]] = {}
        self._next_id = 1
        self._keys: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()  # def endpoints run in a threadpool
        self.open = True

    def close(self) -> None:
        self.open = False

    # orders

    def insert(self, fields: dict[str, Any], created_at: datetime) -> dict[str, Any]:
        with self._lock:
            order = {**fields, "id": self._next_id, "status": "open",
                     "created_at": created_at, "revision": 1}
            self._orders[order["id"]] = order
            self._next_id += 1
            return deepcopy(order)

    def get(self, order_id: int) -> dict[str, Any] | None:
        with self._lock:
            order = self._orders.get(order_id)
            return deepcopy(order) if order else None

    def update_if_revision(self, order_id: int, changes: dict[str, Any],
                           revision: int) -> dict[str, Any] | None:
        """Apply `changes` only if the stored revision is still `revision`.

        Returns the new record, or None when another write came first.
        """
        with self._lock:
            order = self._orders[order_id]
            if order["revision"] != revision:
                return None
            order.update(deepcopy(changes))
            order["revision"] += 1
            return deepcopy(order)

    def page(self, limit: int, after: tuple[datetime, int] | None) -> list[dict[str, Any]]:
        """Newest first by (created_at, id); `after` is the last key already seen."""
        with self._lock:
            rows = sorted(self._orders.values(),
                          key=lambda o: (o["created_at"], o["id"]), reverse=True)
            if after is not None:
                rows = [o for o in rows if (o["created_at"], o["id"]) < after]
            return deepcopy(rows[:limit])

    # idempotency records

    def claim_key(self, key: str, fingerprint: str) -> dict[str, Any] | None:
        """Record `key` as in flight. Returns the existing record if it was seen."""
        with self._lock:
            seen = self._keys.get(key)
            if seen is None:
                self._keys[key] = {"fingerprint": fingerprint, "response": None}
            return deepcopy(seen)

    def finish_key(self, key: str, response: dict[str, Any]) -> None:
        with self._lock:
            self._keys[key]["response"] = deepcopy(response)

    def release_key(self, key: str) -> None:
        with self._lock:
            self._keys.pop(key, None)
