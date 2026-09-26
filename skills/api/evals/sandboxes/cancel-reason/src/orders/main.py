from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


class Order(BaseModel):
    id: int
    status: str
    cancel_reason: str | None = None


ORDERS: dict[int, Order] = {
    1: Order(id=1, status="open"),
    2: Order(id=2, status="shipped"),
}


@app.get("/orders/{order_id}")
def get_order(order_id: int) -> Order:
    if order_id not in ORDERS:
        raise HTTPException(status_code=404, detail="Order not found")
    return ORDERS[order_id]
