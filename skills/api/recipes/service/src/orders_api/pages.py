"""Opaque cursors for keyset pages.

A cursor carries the sort key of the last row a client saw: created_at and
the unique id that breaks ties. Clients must not build or read it; base64
keeps them from relying on its shape, so the server may change it later.
"""

import base64
import binascii
import json
from datetime import datetime

from fastapi.exceptions import RequestValidationError


def encode(created_at: datetime, order_id: int) -> str:
    raw = json.dumps({"t": created_at.isoformat(), "id": order_id}).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode(cursor: str) -> tuple[datetime, int]:
    """The key in `cursor`; a cursor that does not decode is a 422 like any bad parameter."""
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4))
        data = json.loads(raw)
        return datetime.fromisoformat(data["t"]), int(data["id"])
    except (binascii.Error, ValueError, KeyError, TypeError) as e:
        raise RequestValidationError(
            [{"type": "value_error", "loc": ("query", "cursor"),
              "msg": "Invalid cursor", "input": cursor}]
        ) from e
