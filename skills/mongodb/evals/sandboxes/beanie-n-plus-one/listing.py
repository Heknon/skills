"""GET /orders/recent?status=paid: the 50 newest orders with the customer name."""

from models import Order


async def recent_orders(status: str) -> list[dict]:
    orders = await Order.find(Order.status == status).sort(-Order.created_at).limit(50).to_list()
    rows = []
    for order in orders:
        await order.fetch_link(Order.customer)
        rows.append({"id": str(order.id), "total_cents": order.total_cents, "customer": order.customer.name})
    return rows
