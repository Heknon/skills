def line_value(item):
    """Value of one stock line."""
    return item["price"] * item["qty"]


def stock_value(items):
    return sum(line_value(item) for item in items)
