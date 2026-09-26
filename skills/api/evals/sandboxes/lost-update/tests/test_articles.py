from fastapi.testclient import TestClient

from articles.main import app


def test_patch_title():
    with TestClient(app) as client:
        r = client.patch("/articles/1", json={"title": "Offline first, again"})
    assert r.status_code == 200
    assert r.json()["body"] == "Draft"
