from users.models import User
from users.service import patch_user


def stored() -> User:
    return User(id=1, name="Ann Lee", email="ann@example.com")


def test_patch_name_is_tidied():
    assert patch_user(stored(), {"name": "  bea   stone "}).name == "Bea Stone"


def test_patch_email_to_null_clears_it():
    assert patch_user(stored(), {"email": None}).email is None
