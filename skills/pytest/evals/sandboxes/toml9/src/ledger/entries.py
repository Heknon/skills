def balance(entries: list[tuple[str, int]]) -> int:
    return sum(amount if kind == "credit" else -amount for kind, amount in entries)
