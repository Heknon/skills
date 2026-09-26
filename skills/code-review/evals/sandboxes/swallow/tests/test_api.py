from fastapi.testclient import TestClient

from shop.api import app, get_audit, get_store
from shop.notes import AuditLog, NoteStore


def test_note_is_saved_and_audited() -> None:
    store, audit = NoteStore(), AuditLog()
    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_audit] = lambda: audit
    try:
        response = TestClient(app).post("/orders/o-1/notes", json={"text": "gift"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 201
    assert store.notes == {"o-1": ["gift"]}
    assert audit.lines == ["note added to o-1"]
