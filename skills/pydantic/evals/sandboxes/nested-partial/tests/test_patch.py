from users.models import User
from users.service import patch_user


def stored() -> User:
    return User(id=1, name="Ann", address={"street": "1 Rue Haute", "city": "Paris", "postcode": "75001"})


def test_patch_name():
    assert patch_user(stored(), {"name": "Bea"}).name == "Bea"
