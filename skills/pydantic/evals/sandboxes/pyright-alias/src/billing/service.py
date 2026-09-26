from billing.models import Payment


def payment_for(cents: int) -> Payment:
    return Payment(amount_cents=cents, currency="EUR")


def provider_body(payment: Payment) -> dict:
    return payment.model_dump(by_alias=True)
