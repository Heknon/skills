"""Order reports: money formatting, totals, CSV export and the text report.

Everything about reports lives here. It has grown; see README.
"""

import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

__all__ = [
    "CURRENCY_SYMBOLS",
    "Line",
    "Order",
    "format_money",
    "line_total",
    "now",
    "order_total",
    "orders_summary",
    "render_text",
    "stamp_header",
    "tax_for",
    "to_csv_rows",
    "write_csv",
]

# ---------------------------------------------------------------- money

CURRENCY_SYMBOLS = {"EUR": "€", "USD": "$", "GBP": "£"}
CENT = Decimal("0.01")


def _round_cents(amount: Decimal) -> Decimal:
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def format_money(amount: Decimal, currency: str = "EUR") -> str:
    """Format an amount with its symbol: format_money(Decimal("3.5")) -> "€3.50"."""
    symbol = CURRENCY_SYMBOLS.get(currency, currency + " ")
    sign = "-" if amount < 0 else ""
    return f"{sign}{symbol}{_round_cents(abs(amount)):,}"


# ---------------------------------------------------------------- orders


@dataclass
class Line:
    sku: str
    quantity: int
    unit_price: Decimal


@dataclass
class Order:
    number: str
    customer: str
    lines: list[Line] = field(default_factory=list)
    currency: str = "EUR"
    tax_rate: Decimal = Decimal("0.20")


def line_total(line: Line) -> Decimal:
    return _round_cents(line.unit_price * line.quantity)


def tax_for(amount: Decimal, rate: Decimal) -> Decimal:
    return _round_cents(amount * rate)


def order_total(order: Order, with_tax: bool = True) -> Decimal:
    net = sum((line_total(line) for line in order.lines), Decimal("0"))
    if not with_tax:
        return net
    return net + tax_for(net, order.tax_rate)


def orders_summary(orders: list[Order]) -> dict[str, Decimal]:
    """Total with tax per currency, currencies in alphabetical order."""
    totals: dict[str, Decimal] = {}
    for order in orders:
        totals[order.currency] = totals.get(order.currency, Decimal("0")) + order_total(order)
    return dict(sorted(totals.items()))


# ---------------------------------------------------------------- time


def now() -> datetime:
    return datetime.now(timezone.utc)


def stamp_header(title: str) -> str:
    return f"{title} - generated {now():%Y-%m-%d %H:%M} UTC"


# ---------------------------------------------------------------- CSV


def to_csv_rows(orders: list[Order]) -> list[list[str]]:
    rows = [["number", "customer", "currency", "net", "tax", "total"]]
    for order in orders:
        net = order_total(order, with_tax=False)
        tax = tax_for(net, order.tax_rate)
        rows.append([order.number, order.customer, order.currency, str(net), str(tax), str(net + tax)])
    return rows


def write_csv(path: Path, orders: list[Order]) -> int:
    """Write the orders to path; return the number of data rows written."""
    rows = to_csv_rows(orders)
    with path.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(rows)
    return len(rows) - 1


# ---------------------------------------------------------------- text


def render_text(orders: list[Order], title: str = "Orders") -> str:
    lines = [stamp_header(title), ""]
    for order in orders:
        total = format_money(order_total(order), order.currency)
        lines.append(f"{order.number:<8} {order.customer:<20} {total:>12}")
    lines.append("")
    for currency, amount in orders_summary(orders).items():
        lines.append(f"{'total ' + currency:<29} {format_money(amount, currency):>12}")
    return "\n".join(lines)
