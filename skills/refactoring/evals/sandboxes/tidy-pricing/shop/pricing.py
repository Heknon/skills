# pricing helpers used by the shop and the invoicing job
VAT = 0.2


def price_with_vat(net, rate=VAT):
    gross = net + net * rate
    return round(gross, 2)


def add_item(name, price, basket=[]):
    basket.append((name, price))
    return basket


def basket_total(basket):
    t = 0
    for i in range(len(basket)):
        t = t + basket[i][1]
    return t


def fmt(x, currency="EUR"):
    if currency == "EUR":
        return "%.2f EUR" % x
    else:
        if currency == "USD":
            return "$%.2f" % x
        else:
            return "%.2f %s" % (x, currency)


def discount(total, code):
    if code == "SPRING10":
        return total - total * 0.1
    elif code == "VIP":
        return total - total * 0.2
    elif code == None:
        return total
    else:
        return total
