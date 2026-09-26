from fastapi.testclient import TestClient

from notes.main import app


def test_list_notes():
    with TestClient(app) as client:
        assert client.get("/notes").json() == [{"id": 1, "text": "Air gapped"}]
