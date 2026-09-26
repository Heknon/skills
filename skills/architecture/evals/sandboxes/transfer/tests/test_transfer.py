def test_transfer_moves_money(client, accounts):
    assert client.post("/transfers", json={"source_id": 1, "target_id": 2, "amount_cents": 2_500}).status_code == 204
    assert (accounts(1), accounts(2)) == (7_500, 2_500)


def test_insufficient_funds_is_409(client, accounts):
    r = client.post("/transfers", json={"source_id": 2, "target_id": 1, "amount_cents": 1})
    assert r.status_code == 409
