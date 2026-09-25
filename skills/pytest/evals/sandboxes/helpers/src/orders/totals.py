def order_total(lines: list[dict], shipping: float = 4.5) -> dict:
    subtotal = sum(line["price"] * line["qty"] for line in lines)
    return {
        "subtotal": round(subtotal, 2),
        "shipping": 0.0 if subtotal > 50 else shipping,
        "total": round(subtotal + (0.0 if subtotal > 50 else shipping), 2),
    }
