from fastapi.testclient import TestClient

from tickets.main import app


def test_missing_ticket_is_problem_json():
    with TestClient(app) as client:
        r = client.get("/tickets/99")
    assert r.status_code == 404
    assert r.headers["content-type"] == "application/problem+json"
