def is_open(status: str) -> bool:
    return status in {"new", "paid", "packed"}
