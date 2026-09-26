"""Parsing of quantities typed by people: '3', ' 12 ', '1,000'."""


def parse_quantity(text: str) -> int:
    """Return the quantity in `text` as an int.

    Raises ValueError when `text` is not a whole number.
    """
    cleaned = text.strip().replace(",", "")
    if not cleaned.lstrip("-").isdigit():
        raise ValueError(f"not a whole number: {text!r}")
    return int(cleaned)
