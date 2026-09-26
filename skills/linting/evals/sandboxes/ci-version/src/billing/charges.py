import logging
import os
from typing import Optional

log = logging.getLogger(__name__)


def charge(amount: str, note: Optional[str] = None, tags=[]) -> dict:
    try:
        cents = int(amount)
    except Exception:
        log.warning("bad amount %r", amount)
        cents = 0
    return {"cents": cents, "note": note, "tags": tags}
