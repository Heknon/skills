from fastapi import FastAPI, Query

from app import listing

app = FastAPI()


@app.get("/products")
def products(page: int = Query(1, ge=1)) -> list[str]:
    return listing.page(page)
