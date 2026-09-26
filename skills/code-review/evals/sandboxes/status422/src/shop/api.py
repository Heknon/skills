"""HTTP routes for stock."""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from shop.stock import OutOfStock, reserve

app = FastAPI()


class ReserveIn(BaseModel):
    qty: int = Field(gt=0)


class ReserveOut(BaseModel):
    sku: str
    left: int


@app.post("/stock/{sku}/reserve")
def reserve_stock(sku: str, body: ReserveIn) -> ReserveOut:
    try:
        left = reserve(sku, body.qty)
    except OutOfStock as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"only {exc.left} left",
        ) from exc
    return ReserveOut(sku=sku, left=left)
