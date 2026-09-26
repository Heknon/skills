import pytest
from pydantic import ValidationError

from users.models import User
from users.service import create_user, patch_user


def test_create_rejects_short_name():
    with pytest.raises(ValidationError):
        create_user({"id": 1, "name": "Al"})


def test_patch_keeps_other_fields():
    stored = User(id=1, name="Ann", email="ann@example.com")
    assert patch_user(stored, {"name": "Bea"}).email == "ann@example.com"
