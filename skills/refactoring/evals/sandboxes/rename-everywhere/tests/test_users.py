from unittest import mock

from app import profile, users
from app.users import get_user


def test_get_user_found():
    assert get_user(1)["name"] == "Ada"


def test_get_user_missing():
    assert get_user(99) is None


def test_list_users_active_only():
    assert [u["id"] for u in users.list_users(active_only=True)] == [1]


def test_display_name_uses_lookup():
    with mock.patch("app.users.get_user", return_value={"id": 7, "name": "Mock"}):
        assert profile.display_name(7) == "Mock"
