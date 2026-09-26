from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.billing.repository import InvoiceRepository, get_invoice_repository
from app.billing.service import BillingService

router = APIRouter(prefix="/invoices", tags=["billing"])


def get_billing_service(repo: Annotated[InvoiceRepository, Depends(get_invoice_repository)]) -> BillingService:
    return BillingService(repo)


ServiceDep = Annotated[BillingService, Depends(get_billing_service)]


class InvoiceOut(BaseModel):
    id: int
    customer_id: int
    amount_cents: int
    paid: bool


@router.get("/{invoice_id}")
def get_invoice(invoice_id: int, service: ServiceDep) -> InvoiceOut:
    invoice = service.get_invoice(invoice_id)
    return InvoiceOut.model_validate(invoice, from_attributes=True)


@router.post("/{invoice_id}/pay")
def pay_invoice(invoice_id: int, service: ServiceDep) -> InvoiceOut:
    return InvoiceOut.model_validate(service.pay(invoice_id), from_attributes=True)
