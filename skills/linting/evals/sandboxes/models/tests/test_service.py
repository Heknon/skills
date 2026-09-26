from accounts.service import from_row, from_wire


def test_from_row() -> None:
    user = from_row((1, "Ada", "ada@example.com"))
    assert user.display_name == "Ada"


def test_from_wire_uses_the_alias() -> None:
    user = from_wire({"id": 1, "displayName": "Ada", "email": "ada@example.com"})
    assert user.display_name == "Ada"
