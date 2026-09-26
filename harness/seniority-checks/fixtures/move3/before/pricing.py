TIERS = ("basic", "pro")
rates = {"basic": 1.0, "pro": 0.8}


def tier(name):
    return rates[name]
