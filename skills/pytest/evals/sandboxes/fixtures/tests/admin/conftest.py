import pytest


@pytest.fixture
def user(user):
    return dict(user, role="admin")
