from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.invoices.models import Invoice
from app.invoices.schemas import InvoiceIn


class InvoiceRepository:
    async def get_by_number(self, number: str) -> Invoice | None:
        return await Invoice.find_one(Invoice.number == number)

    async def create(self, data: InvoiceIn) -> Invoice:
        try:
            return await Invoice(**data.model_dump()).insert()
        except DuplicateKeyError:
            raise HTTPException(409, f"invoice {data.number} already exists")

    async def totals_by_customer(self) -> list[dict]:
        return await Invoice.aggregate([
            {"$match": {"paid": False}},
            {"$group": {"_id": "$customer_id", "open_cents": {"$sum": "$amount_cents"}}},
        ]).to_list()
