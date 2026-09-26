from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()

STOCK: dict[str, int] = {"bolt": 10, "nut": 0}
ORDERS: dict[int, dict] = {}


class OrderIn(BaseModel):
    sku: str
    quantity: int = Field(ge=1)


class Order(OrderIn):
    id: int


@app.post("/orders", status_code=201)
def place_order(body: OrderIn) -> Order:
    if body.sku not in STOCK:
        raise HTTPException(status_code=404, detail="Unknown SKU")
    if STOCK[body.sku] < body.quantity:
        raise HTTPException(status_code=409, detail="Not enough stock")
    STOCK[body.sku] -= body.quantity
    order = {"id": len(ORDERS) + 1, "sku": body.sku, "quantity": body.quantity}
    ORDERS[order["id"]] = order
    return Order(**order)


@app.get("/orders/{order_id}")
def get_order(order_id: int) -> Order:
    if order_id not in ORDERS:
        raise HTTPException(status_code=404, detail="Order not found")
    return Order(**ORDERS[order_id])
