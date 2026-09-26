from fastapi.testclient import TestClient

from members.main import app


def test_list_members():
    with TestClient(app) as client:
        r = client.get("/members")
    assert r.status_code == 200
    assert r.json() == [{"id": 1, "name": "Ann"}, {"id": 2, "name": "Bea"}]
