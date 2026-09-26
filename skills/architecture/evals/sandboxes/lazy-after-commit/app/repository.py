from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Order, OrderLine


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, customer: str, lines: list[tuple[str, int]]) -> Order:
        order = Order(customer=customer, lines=[OrderLine(sku=s, quantity=q) for s, q in lines])
        self.session.add(order)
        await self.session.commit()
        return order

    async def get(self, order_id: int) -> Order | None:
        return await self.session.scalar(select(Order).where(Order.id == order_id))
