TIERS = ("basic", "pro")


def tier(name):
    return {"basic": 1.0, "pro": 0.8}[name]
