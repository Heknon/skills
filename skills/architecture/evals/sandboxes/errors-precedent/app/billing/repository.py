from dataclasses import dataclass

from fastapi import Request


@dataclass
class Invoice:
    id: int
    customer_id: int
    amount_cents: int
    paid: bool = False


class InvoiceRepository:
    """In memory until the database lands; one instance per app (app.state)."""

    def __init__(self) -> None:
        self._rows = {1: Invoice(id=1, customer_id=1, amount_cents=5_000)}

    def get(self, invoice_id: int) -> Invoice | None:
        return self._rows.get(invoice_id)


def get_invoice_repository(request: Request) -> InvoiceRepository:
    return request.app.state.invoices
