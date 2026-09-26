from users.models import User
from users.service import patch_user


def stored() -> User:
    return User(id=1, name="Ann", email="ann@example.com", status="suspended")


def test_patch_changes_name():
    assert patch_user(stored(), {"name": "Xavier"}).name == "Xavier"
