import pytest

from greeting.banner import banner


def test_banner_names_the_user(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_USER", "ada")
    assert banner() == "Welcome back, ada!"
