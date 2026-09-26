from fastapi.testclient import TestClient

from profiles.main import app


def test_update_bio():
    with TestClient(app) as client:
        r = client.patch("/profiles/1", json={"display_name": "Ann", "bio": "Runner"})
    assert r.status_code == 200
    assert r.json()["bio"] == "Runner"
