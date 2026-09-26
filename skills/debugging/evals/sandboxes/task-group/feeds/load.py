import asyncio
import json
from datetime import date
from pathlib import Path

DATA = Path(__file__).parent.parent / "data"


async def read_feed(name):
    """Stands in for an HTTP call: the feed's JSON from data/."""
    await asyncio.sleep(0.01)
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))


async def prices():
    feed = await read_feed("prices")
    return {item["sku"]: item["price"] for item in feed["items"]}


async def stock():
    feed = await read_feed("stock")
    return {item["sku"]: item["quantity"] for item in feed["items"]}


async def deliveries():
    feed = await read_feed("deliveries")
    return [(item["sku"], date.fromisoformat(item["expected"])) for item in feed["items"]]
