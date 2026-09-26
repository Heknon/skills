from app.core.errors import ConflictError


class InvoiceAlreadyPaidError(ConflictError):
    code = "invoice_already_paid"

    def __init__(self, invoice_id: int) -> None:
        super().__init__(invoice_id)
        self.invoice_id = invoice_id

    def __str__(self) -> str:
        return f"invoice {self.invoice_id} is already paid"
