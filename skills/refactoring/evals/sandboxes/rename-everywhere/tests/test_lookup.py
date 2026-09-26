from app.lookup import resolve


class EmptyCache:
    pass


def test_resolve_without_finder_is_unknown():
    assert resolve(5, source=EmptyCache()) == {"id": 5, "name": "unknown"}
