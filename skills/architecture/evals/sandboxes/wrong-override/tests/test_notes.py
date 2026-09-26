from fastapi.testclient import TestClient

from app.main import app
from app.repository import NoteRepository


class FakeNotes:
    def get(self, note_id: int) -> dict | None:
        return {"id": note_id, "title": "fake"} if note_id == 1 else None


def test_read_note():
    app.dependency_overrides[NoteRepository] = FakeNotes
    with TestClient(app) as client:
        r = client.get("/notes/1")
    assert r.status_code == 200
    assert r.json() == {"id": 1, "title": "fake"}


def test_missing_note_is_404():
    app.dependency_overrides[NoteRepository] = FakeNotes
    with TestClient(app) as client:
        assert client.get("/notes/2").status_code == 404
