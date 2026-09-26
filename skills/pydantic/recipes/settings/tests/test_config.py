import os

import pytest

from app.config import Settings, get_settings


@pytest.fixture(autouse=True)
def fresh_settings(monkeypatch):
    """No developer .env, no leftover APP_ variables, no cached settings."""
    for name in list(os.environ):
        if name.upper().startswith("APP_"):
            monkeypatch.delenv(name)
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_defaults():
    s = get_settings()
    assert (s.port, s.environment, s.db.host) == (8000, "dev", "localhost")


def test_environment_variable_wins(monkeypatch):
    monkeypatch.setenv("APP_PORT", "9001")
    monkeypatch.setenv("APP_DB__HOST", "db.internal")
    s = get_settings()
    assert s.port == 9001
    assert s.db.host == "db.internal"
    assert s.db.name == "app"  # nested values merge with the defaults


def test_init_argument_beats_environment(monkeypatch):
    monkeypatch.setenv("APP_PORT", "9001")
    assert Settings(port=7000).port == 7000


def test_dotenv_file(tmp_path):
    env = tmp_path / ".env"
    env.write_text("APP_PORT=7100\nCOMPOSE_PROJECT_NAME=x\n", encoding="utf-8")
    assert Settings(_env_file=env).port == 7100


def test_dotenv_typo_fails(tmp_path):
    env = tmp_path / ".env"
    env.write_text("APP_PROT=7100\n", encoding="utf-8")
    with pytest.raises(Exception, match="extra_forbidden"):
        Settings(_env_file=env)


def test_password_is_masked(monkeypatch):
    monkeypatch.setenv("APP_DB_PASSWORD", "hunter2")
    s = get_settings()
    assert "hunter2" not in repr(s)
    assert "hunter2" not in str(s.model_dump())
    assert s.db_password.get_secret_value() == "hunter2"
