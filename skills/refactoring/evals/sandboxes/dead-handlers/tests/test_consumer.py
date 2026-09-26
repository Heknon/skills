from events.consumer import dispatch


def test_refund_is_dispatched():
    assert dispatch({"kind": "refund", "id": 7, "amount": "9.50"}) == "refund 7: 9.50"
