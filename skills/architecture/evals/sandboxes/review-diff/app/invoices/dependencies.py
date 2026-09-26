from typing import Annotated

from fastapi import Depends

from app.invoices.repository import InvoiceRepository
from app.invoices.service import InvoiceService


def get_invoice_repository() -> InvoiceRepository:
    return InvoiceRepository()


def get_invoice_service(repo: Annotated[InvoiceRepository, Depends(get_invoice_repository)]) -> InvoiceService:
    return InvoiceService(repo)
