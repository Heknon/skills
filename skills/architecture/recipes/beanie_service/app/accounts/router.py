"""HTTP only: parse, call the service once, map the result to a schema."""

from fastapi import APIRouter

from app.accounts.dependencies import AccountServiceDep
from app.accounts.schemas import AccountIn, AccountOut, TransferIn

router = APIRouter(tags=["accounts"])


@router.post("/accounts", status_code=201)
async def open_account(body: AccountIn, service: AccountServiceDep) -> AccountOut:
    return AccountOut.from_domain(
        await service.open_account(body.owner_email, body.kyc_reference)
    )


@router.get("/accounts/{account_id}")
async def get_account(account_id: str, service: AccountServiceDep) -> AccountOut:
    return AccountOut.from_domain(await service.get(account_id))


@router.post("/transfers", status_code=204)
async def transfer(body: TransferIn, service: AccountServiceDep) -> None:
    await service.transfer(body.source_id, body.target_id, body.amount_cents)
