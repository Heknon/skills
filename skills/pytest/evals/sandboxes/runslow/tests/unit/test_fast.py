from app.net import ping


def test_ping():
    assert ping() == "pong"
