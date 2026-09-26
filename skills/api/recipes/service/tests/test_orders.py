from fastapi.testclient import TestClient

from orders_api.deps import get_store
from orders_api.main import app
from orders_api.routes import fingerprint

PROBLEM = "application/problem+json"


def create(client: TestClient, **fields) -> dict:
    r = client.post("/orders", json={"customer": "acme", "quantity": 2, **fields})
    assert r.status_code == 201, r.text
    return r.json()


# create


def test_create_returns_201_with_location(client):
    r = client.post("/orders", json={"customer": "acme", "quantity": 2})
    assert r.status_code == 201
    assert r.headers["location"] == f"/orders/{r.json()['id']}"
    assert r.json()["status"] == "open"


def test_server_owned_field_in_body_is_422_problem(client):
    body = {"customer": "acme", "quantity": 2, "status": "cancelled"}
    r = client.post("/orders", json=body)
    assert r.status_code == 422
    assert r.headers["content-type"] == PROBLEM
    assert r.json()["title"] == "Unprocessable Content"
    assert r.json()["errors"] == [
        {"loc": ["body", "status"], "type": "extra_forbidden",
         "msg": "Extra inputs are not permitted"}
    ]


def test_retry_with_same_key_creates_one_order(client):
    body = {"customer": "acme", "quantity": 2}
    first = client.post("/orders", json=body, headers={"Idempotency-Key": "k1"})
    again = client.post("/orders", json=body, headers={"Idempotency-Key": "k1"})
    assert first.status_code == again.status_code == 201
    assert again.json() == first.json()
    assert len(client.get("/orders").json()["items"]) == 1


def test_same_key_with_other_body_is_422(client):
    key = {"Idempotency-Key": "k1"}
    client.post("/orders", json={"customer": "acme", "quantity": 2}, headers=key)
    r = client.post("/orders", json={"customer": "acme", "quantity": 3}, headers=key)
    assert r.status_code == 422


def test_same_key_while_first_is_in_flight_is_409(client):
    body = {"customer": "acme", "quantity": 2, "note": None}
    client.app.state.store.claim_key("k1", fingerprint(body))  # the first request, still running
    r = client.post("/orders", json=body, headers={"Idempotency-Key": "k1"})
    assert r.status_code == 409


# read


def test_get_returns_etag_and_404_is_a_problem(client):
    order = create(client)
    r = client.get(f"/orders/{order['id']}")
    assert r.headers["etag"] == '"1"'
    missing = client.get("/orders/999")
    assert missing.status_code == 404
    assert missing.headers["content-type"] == PROBLEM
    assert missing.json()["detail"] == "Order 999 not found"


# list


def test_pages_cover_every_order_once_across_ties(client, frozen_clock):
    ids = {create(client)["id"] for _ in range(25)}      # all share one created_at
    seen, cursor, pages = [], None, 0
    while pages < 5:                                      # bounded: a bad cursor must not hang
        params = {"limit": 10, **({"cursor": cursor} if cursor else {})}
        page = client.get("/orders", params=params).json()
        seen += [o["id"] for o in page["items"]]
        pages += 1
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert pages == 3
    assert sorted(seen) == sorted(ids)                    # no repeats, none missing
    assert seen == sorted(seen, reverse=True)             # ties ordered by id


def test_bad_cursor_and_limit_are_422(client):
    assert client.get("/orders", params={"cursor": "not-a-cursor"}).status_code == 422
    assert client.get("/orders", params={"limit": 101}).status_code == 422


# patch


def test_patch_changes_only_what_was_sent(client):
    order = create(client, note="first")
    r = client.patch(f"/orders/{order['id']}", json={"quantity": 5})
    assert r.status_code == 200
    assert (r.json()["quantity"], r.json()["note"], r.json()["customer"]) == (5, "first", "acme")
    assert r.headers["etag"] == '"2"'


def test_patch_null_clears(client):
    order = create(client, note="first")
    r = client.patch(f"/orders/{order['id']}", json={"note": None})
    assert r.json()["note"] is None


def test_patch_invalid_result_is_422_not_500(client):
    order = create(client)
    for body, loc in [({"quantity": None}, ["body", "quantity"]),
                      ({"quantity": 0}, ["body", "quantity"]),
                      ({"status": "cancelled"}, ["body", "status"])]:
        r = client.patch(f"/orders/{order['id']}", json=body)
        assert r.status_code == 422, body
        assert r.json()["errors"][0]["loc"] == loc


def test_patch_accepts_merge_patch_media_type(client):
    order = create(client, note="x")
    r = client.patch(f"/orders/{order['id']}", content=b'{"note": null}',
                     headers={"Content-Type": "application/merge-patch+json"})
    assert r.status_code == 200
    assert r.json()["note"] is None


def test_patch_with_stale_etag_is_412(client):
    order = create(client)
    tag = client.get(f"/orders/{order['id']}").headers["etag"]
    first = client.patch(f"/orders/{order['id']}", json={"quantity": 3}, headers={"If-Match": tag})
    second = client.patch(f"/orders/{order['id']}", json={"quantity": 4}, headers={"If-Match": tag})
    assert first.status_code == 200
    assert second.status_code == 412


def test_if_match_star_and_lists(client):
    order = create(client)
    url = f"/orders/{order['id']}"
    assert client.patch(url, json={"quantity": 3}, headers={"If-Match": "*"}).status_code == 200
    listed = {"If-Match": '"9", "2"'}
    assert client.patch(url, json={"quantity": 4}, headers=listed).status_code == 200
    assert client.patch(url, json={"quantity": 5}, headers={"If-Match": 'W/"3"'}).status_code == 412


def test_patch_retries_when_another_write_wins(client, monkeypatch):
    order = create(client)
    store = client.app.state.store
    real, calls = store.update_if_revision, []

    def lose_first_race(order_id, changes, revision):
        calls.append(revision)
        if len(calls) == 1:
            real(order_id, {"customer": "other writer"}, revision)  # someone else wins
            return None
        return real(order_id, changes, revision)

    monkeypatch.setattr(store, "update_if_revision", lose_first_race)
    r = client.patch(f"/orders/{order['id']}", json={"quantity": 9})
    assert r.status_code == 200
    assert (r.json()["customer"], r.json()["quantity"]) == ("other writer", 9)
    assert calls == [1, 2]


def test_patch_gives_up_with_409(client, monkeypatch):
    order = create(client)
    monkeypatch.setattr(client.app.state.store, "update_if_revision", lambda *a: None)
    assert client.patch(f"/orders/{order['id']}", json={"quantity": 9}).status_code == 409


def test_patch_cancelled_order_is_409(client):
    order = create(client)
    client.post(f"/orders/{order['id']}/cancel", json={"reason": "late"})
    assert client.patch(f"/orders/{order['id']}", json={"quantity": 3}).status_code == 409


# cancel


def test_cancel_twice_is_the_same_result(client):
    order = create(client)
    first = client.post(f"/orders/{order['id']}/cancel", json={"reason": "late"})
    again = client.post(f"/orders/{order['id']}/cancel", json={"reason": "late"})
    assert first.status_code == again.status_code == 200
    assert again.json() == first.json()
    assert first.json()["cancel_reason"] == "late"


# errors the router raises itself


def test_unknown_path_and_wrong_method_are_problems(client):
    r = client.get("/nothing")
    assert (r.status_code, r.headers["content-type"]) == (404, PROBLEM)
    r = client.delete("/orders/1")
    assert (r.status_code, r.headers["content-type"]) == (405, PROBLEM)
    # Allow names only the first route that matched the path (GET), not PATCH
    assert r.headers["allow"] == "GET"


def test_unhandled_error_is_500_problem_without_the_message():
    def broken():
        raise RuntimeError("password=hunter2")

    app.dependency_overrides[get_store] = broken
    with TestClient(app, raise_server_exceptions=False) as client:
        r = client.get("/orders/1")
    assert (r.status_code, r.headers["content-type"]) == (500, PROBLEM)
    assert "hunter2" not in r.text


# contract and lifecycle


def test_openapi_shows_bodies_where_they_belong():
    spec = app.openapi()
    cancel = spec["paths"]["/orders/{order_id}/cancel"]["post"]
    assert [p["name"] for p in cancel["parameters"]] == ["order_id"]
    assert cancel["requestBody"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/CancelRequest"
    }
    post = spec["paths"]["/orders"]["post"]
    assert "idempotency-key" in [p["name"] for p in post["parameters"]]


def test_lifespan_closes_the_store():
    with TestClient(app) as client:
        store = client.app.state.store
        assert store.open
    assert not store.open
