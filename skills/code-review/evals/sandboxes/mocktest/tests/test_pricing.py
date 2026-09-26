from shop import pricing


def test_with_vat_for_belgium() -> None:
    assert pricing.with_vat(1_000, "BE") == 1_210
