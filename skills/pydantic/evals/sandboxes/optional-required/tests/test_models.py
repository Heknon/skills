import pytest
from pydantic import ValidationError

from profiles.models import ProfileIn


def test_full_body():
    p = ProfileIn.model_validate({"username": "ann", "nickname": "a", "referrer": None})
    assert p.nickname == "a"


def test_referrer_must_be_sent():
    with pytest.raises(ValidationError):
        ProfileIn.model_validate({"username": "ann", "nickname": "a"})
