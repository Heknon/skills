from shop.points import AUDIT, audit


def test_audit_keeps_lines() -> None:
    audit("hello")
    assert AUDIT[-1] == "hello"
