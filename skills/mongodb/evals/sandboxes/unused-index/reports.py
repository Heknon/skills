"""Regional sales report. Runs on the analytics replica set member
(readPreference=secondary in REPORTS_URI) so it never loads the primary."""

from models import Order


async def orders_in(country: str) -> list[Order]:
    return await Order.find(Order.country == country).to_list()
