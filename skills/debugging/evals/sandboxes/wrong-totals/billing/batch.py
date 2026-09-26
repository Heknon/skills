import json
import sys

from billing.invoice import build_invoice


def run(path):
    with open(path, encoding="utf-8") as f:
        orders = json.load(f)
    for order in orders:
        if order.get("balance"):
            invoice = build_invoice(
                order["customer"], order["items"], [("balance", order["balance"])]
            )
        else:
            invoice = build_invoice(order["customer"], order["items"])
        print(f"{invoice['customer']:<8} {invoice['total']:>8.2f}")


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "orders.json")
