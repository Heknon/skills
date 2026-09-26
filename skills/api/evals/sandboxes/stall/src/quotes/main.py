import time

from fastapi import FastAPI, HTTPException

from quotes.rates import fetch_rate

app = FastAPI()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/quotes/{currency}")
async def quote(currency: str, amount: float = 1.0) -> dict:
    if currency not in {"EUR", "USD", "GBP"}:
        raise HTTPException(status_code=404, detail="Unknown currency")
    rate = fetch_rate(currency)
    time.sleep(0.1)  # rate limit towards the legacy service
    return {"currency": currency, "amount": round(amount * rate, 2)}
