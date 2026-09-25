from events.dispatch import dispatch


def refund(order_id):
    return dispatch({"kind": "refund", "id": order_id})
