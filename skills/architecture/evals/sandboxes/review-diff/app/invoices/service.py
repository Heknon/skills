from app.invoices.models import Invoice
from app.invoices.repository import InvoiceRepository
from app.invoices.schemas import InvoiceIn


class InvoiceService:
    """Every route goes through the service, even when it only forwards (team rule, see README)."""

    def __init__(self, repo: InvoiceRepository) -> None:
        self.repo = repo

    async def get(self, number: str) -> Invoice | None:
        return await self.repo.get_by_number(number)

    async def create(self, data: InvoiceIn) -> Invoice:
        return await self.repo.create(data)

    async def totals_by_customer(self) -> list[dict]:
        return await self.repo.totals_by_customer()
