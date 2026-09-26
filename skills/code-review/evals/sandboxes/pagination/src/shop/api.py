"""HTTP routes for the catalogue."""

from fastapi import FastAPI
from pydantic import BaseModel

from shop.catalog import all_products

app = FastAPI()


class ProductOut(BaseModel):
    sku: str
    name: str
    price_cents: int


@app.get("/products")
def list_products() -> list[ProductOut]:
    return [
        ProductOut(sku=p.sku, name=p.name, price_cents=p.price_cents)
        for p in all_products()
    ]
