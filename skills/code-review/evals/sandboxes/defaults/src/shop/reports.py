"""Lines for the monthly customer report."""

from shop.orders import list_orders, revenue_cents


def report_line(customer_id: str) -> str:
    orders = list_orders(customer_id)
    return f"{customer_id}: {len(orders)} orders, {revenue_cents(customer_id)} cents"
