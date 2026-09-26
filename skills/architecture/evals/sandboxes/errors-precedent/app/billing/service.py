from app.billing.errors import InvoiceAlreadyPaidError
from app.billing.repository import Invoice, InvoiceRepository


class BillingService:
    def __init__(self, repo: InvoiceRepository) -> None:
        self.repo = repo

    def get_invoice(self, invoice_id: int) -> Invoice | None:
        return self.repo.get(invoice_id)

    def pay(self, invoice_id: int) -> Invoice:
        invoice = self.repo.get(invoice_id)
        if invoice.paid:
            raise InvoiceAlreadyPaidError(invoice_id)
        invoice.paid = True
        return invoice
