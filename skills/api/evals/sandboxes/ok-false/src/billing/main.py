from fastapi import FastAPI

app = FastAPI()

CUSTOMERS = {1: {"id": 1, "name": "Acme"}}
INVOICES = {10: {"id": 10, "customer_id": 1, "total_cents": 12000, "status": "open"}}


@app.get("/customers/{customer_id}")
def get_customer(customer_id: int) -> dict:
    customer = CUSTOMERS.get(customer_id)
    if customer is None:
        return {"ok": False, "error": "customer not found"}
    return {"ok": True, "data": customer}


@app.post("/customers/{customer_id}/block")
def block_customer(customer_id: int) -> dict:
    if customer_id not in CUSTOMERS:
        return {"ok": False, "error": "customer not found"}
    CUSTOMERS[customer_id]["blocked"] = True
    return {"ok": True, "data": CUSTOMERS[customer_id]}
