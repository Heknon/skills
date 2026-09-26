def build_invoice(customer, items, lines=[]):
    """Invoice lines and total for one customer.

    `lines` may hold lines carried over from earlier, such as an unpaid
    balance, as (label, amount) pairs.
    """
    for item in items:
        lines.append((item["sku"], item["qty"] * item["price"]))
    total = round(sum(amount for _, amount in lines), 2)
    return {"customer": customer, "lines": lines, "total": total}
