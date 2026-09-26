"""In-memory stand-in for the document store.

Every document carries a revision that the store increments on each write.
"""

from copy import deepcopy

_DOCS: dict[int, dict] = {
    1: {"id": 1, "title": "Offline first", "body": "Draft", "tags": ["ops"], "revision": 1},
}


def get(doc_id: int) -> dict | None:
    doc = _DOCS.get(doc_id)
    return deepcopy(doc) if doc else None


def replace(doc_id: int, doc: dict) -> dict:
    """Write unconditionally."""
    doc = {**doc, "revision": _DOCS[doc_id]["revision"] + 1}
    _DOCS[doc_id] = deepcopy(doc)
    return doc


def replace_if_revision(doc_id: int, doc: dict, revision: int) -> dict | None:
    """Write only if the stored revision is still `revision`; None if it moved on."""
    if _DOCS[doc_id]["revision"] != revision:
        return None
    return replace(doc_id, doc)
