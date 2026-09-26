def line_total(price_cents: int, qty: int) -> int:
    return price_cents * qty


def cart_total(lines: list[tuple[int, int]]) -> int:
    return sum(line_total(p, q) for p, q in lines)
