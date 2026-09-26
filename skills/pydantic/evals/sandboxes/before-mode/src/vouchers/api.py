"""A stand-in for the web layer: a ValidationError becomes a 422."""

from pydantic import ValidationError

from vouchers.models import Voucher


def create_voucher(body: dict) -> tuple[int, dict]:
    try:
        voucher = Voucher.model_validate(body)
    except ValidationError as exc:
        return 422, {"errors": exc.errors(include_url=False)}
    return 201, voucher.model_dump()
