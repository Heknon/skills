from svc import settings


def test_timeout_from_env(monkeypatch):
    monkeypatch.setenv("SVC_TIMEOUT", "5")
    assert settings.load()["timeout"] == 5


def test_default_timeout():
    assert settings.load()["timeout"] == 30
