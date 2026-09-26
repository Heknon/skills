import datetime as dt
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.invoices.schemas import InvoiceIn, InvoiceOut
from app.invoices.dependencies import get_invoice_service
from app.invoices.models import Invoice
from app.invoices.service import InvoiceService

router = APIRouter(prefix="/invoices", tags=["invoices"])
ServiceDep = Annotated[InvoiceService, Depends(get_invoice_service)]


@router.get("/overdue")
async def overdue_invoices() -> list[InvoiceOut]:
    today = dt.date.today()
    rows = await Invoice.find(Invoice.paid == False, Invoice.due < today).to_list()  # noqa: E712
    return [InvoiceOut.model_validate(r.model_dump()) for r in rows]


@router.get("/open-totals")
async def open_totals(service: ServiceDep) -> list[dict]:
    rows = await service.totals_by_customer()
    return [{"customer_id": r["_id"], "open_cents": r["open_cents"]} for r in rows]


@router.get("/{number}")
async def get_invoice(number: str, service: ServiceDep) -> InvoiceOut:
    invoice = await service.get(number)
    if invoice is None:
        raise HTTPException(404, f"invoice {number} not found")
    return InvoiceOut.model_validate(invoice.model_dump())


@router.post("", status_code=201)
async def create_invoice(body: InvoiceIn, service: ServiceDep) -> InvoiceOut:
    invoice = await service.create(body)
    return InvoiceOut.model_validate(invoice.model_dump())
