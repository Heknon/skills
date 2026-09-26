import asyncio

from feeds.load import deliveries, prices, stock


async def main():
    async with asyncio.TaskGroup() as tg:
        p = tg.create_task(prices())
        s = tg.create_task(stock())
        d = tg.create_task(deliveries())
    for sku, price in sorted(p.result().items()):
        print(f"{sku}  {price:8.2f}  in stock {s.result().get(sku, 0)}")
    for sku, when in d.result():
        print(f"{sku}  expected {when}")


asyncio.run(main())
