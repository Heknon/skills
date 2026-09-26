"""What the web layer calls."""

from decimal import Decimal

from app.reports import Order, format_money, render_text


def report_page(orders: list[Order]) -> str:
    return render_text(orders, title="Daily orders")


def price_label(amount_text: str, currency: str) -> str:
    return format_money(Decimal(amount_text), currency)
