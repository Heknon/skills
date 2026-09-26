from tables import rates as rates

TIERS = ("basic", "pro")


def tier(name):
    return rates[name]
