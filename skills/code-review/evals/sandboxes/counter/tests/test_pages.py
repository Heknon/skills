from typing import Any

from shop.pages import record_view


class FakePages:
    """Enough of a pymongo Collection for these tests, one thread only."""

    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self.docs = docs

    def _match(self, query: dict[str, Any]) -> dict[str, Any] | None:
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None

    def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        doc = self._match(query)
        return dict(doc) if doc else None

    def update_one(self, query: dict[str, Any], update: dict[str, Any]) -> None:
        doc = self._match(query)
        if doc is not None:
            doc.update(update["$set"])

    def find_one_and_update(
        self, query: dict[str, Any], update: dict[str, Any], **_: Any
    ) -> dict[str, Any] | None:
        doc = self._match(query)
        if doc is None:
            return None
        for key, step in update["$inc"].items():
            doc[key] = doc.get(key, 0) + step
        return dict(doc)


def test_record_view_counts() -> None:
    pages = FakePages([{"_id": 1, "slug": "home", "views": 41}])
    assert record_view(pages, "home") == 42  # type: ignore[arg-type]
    assert record_view(pages, "home") == 43  # type: ignore[arg-type]
