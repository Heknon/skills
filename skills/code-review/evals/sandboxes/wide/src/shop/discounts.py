"""Discounts on an order total."""


def discounted_cents(total_cents: int, coupon: str | None) -> int:
    """The total after a coupon: WELCOME10 takes 10% off."""
    if coupon == "WELCOME10":
        return total_cents - total_cents // 10
    return total_cents
