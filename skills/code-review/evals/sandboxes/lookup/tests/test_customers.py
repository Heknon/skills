import pytest

from shop.customers import CustomerNotFound, find_customer


def test_find_customer_ignores_case_and_spaces() -> None:
    assert find_customer("  Ann@Example.com ").name == "Ann Lee"


def test_find_customer_unknown_email_raises() -> None:
    with pytest.raises(CustomerNotFound):
        find_customer("nobody@example.com")
