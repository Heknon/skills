from billing.models import Payment
from billing.service import payment_for, provider_body


def test_payment_for():
    assert payment_for(250).amount_cents == 250


def test_provider_body_uses_camel_case():
    assert provider_body(payment_for(250)) == {"amountCents": 250, "currency": "EUR"}


def test_provider_input():
    assert Payment.model_validate({"amountCents": 5, "currency": "EUR"}).amount_cents == 5
