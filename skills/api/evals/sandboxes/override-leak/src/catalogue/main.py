from typing import Annotated

from fastapi import Depends, FastAPI

app = FastAPI()


def get_price_list() -> dict[str, float]:
    """The real price list; in production it is read from the pricing service."""
    return {"apple": 0.5, "pear": 0.75}


PriceList = Annotated[dict[str, float], Depends(get_price_list)]


@app.get("/prices/{item}")
def price(item: str, prices: PriceList) -> dict:
    return {"item": item, "price": prices.get(item)}
