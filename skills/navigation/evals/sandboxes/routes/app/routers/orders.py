from app.router import Router

router = Router(prefix="/orders")


@router.get("/{order_id}")
def get_order(order_id):
    return {"id": order_id}


@router.post("/{order_id}/refund")
def refund_order(order_id):
    return {"id": order_id, "refunded": True}
