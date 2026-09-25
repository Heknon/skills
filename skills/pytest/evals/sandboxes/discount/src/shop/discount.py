RATES = {"basic": 0.0, "silver": 0.1, "gold": 0.2}


def rate_for(tier: str) -> float:
    return RATES[tier]


def apply_discount(price: float, tier: str) -> float:
    """Price after the tier's discount, rounded to cents."""
    return round(price * (1 - rate_for(tier)), 2)
