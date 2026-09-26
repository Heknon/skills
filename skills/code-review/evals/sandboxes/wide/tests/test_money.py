from shop.discounts import discounted_cents
from shop.jobs.job_01 import run_01
from shop.tax import vat_cents


def test_welcome_coupon() -> None:
    assert discounted_cents(5_000, "WELCOME10") == 4_500


def test_no_coupon() -> None:
    assert discounted_cents(5_000, None) == 5_000


def test_vat() -> None:
    assert vat_cents(1_000, 21) == 210


def test_a_job_runs() -> None:
    assert run_01([1, 2, 3]) == 3
