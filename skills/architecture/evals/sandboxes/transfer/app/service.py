from app.repository import AccountRepository


class TransferService:
    def __init__(self, accounts: AccountRepository) -> None:
        self.accounts = accounts

    async def transfer(self, source_id: int, target_id: int, amount_cents: int) -> None:
        await self.accounts.debit(source_id, amount_cents)
        await self.accounts.credit(target_id, amount_cents)
