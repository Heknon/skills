"""Page view counters, stored in MongoDB."""

from typing import Any

from pymongo import ReturnDocument
from pymongo.collection import Collection

PageDoc = dict[str, Any]


def record_view(pages: Collection[PageDoc], slug: str) -> int:
    """Count one view of the page; return the new count, or 0 for no page."""
    page = pages.find_one_and_update(
        {"slug": slug},
        {"$inc": {"views": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if page is None:
        return 0
    return int(page["views"])
