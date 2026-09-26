import datetime as dt

import pytest

from app.db import init_db
from app.models import Address, Customer, Order
from app.queries import Conflict, add_points, customer_cards, patch_customer, recent_orders
from conftest import DB, URI


async def fresh(n_customers: int = 20, n_orders: int = 200):
    client = await init_db(URI, DB, build_indexes=True)
    await client.drop_database(DB)
    client = await init_db(URI, DB, build_indexes=True)
    customers = [Customer(name=f"C{i}", email=f"c{i}@example.com",
                          address=Address(street=f"{i} Main St", city="Paris" if i % 2 else "Lyon", zip="75001"))
                 for i in range(n_customers)]
    await Customer.insert_many(customers)
    customers = await Customer.find_all().to_list()
    start = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
    await Order.insert_many([Order(customer=customers[i % n_customers], status="paid" if i % 3 else "pending",
                                   total_cents=i, created_at=start + dt.timedelta(minutes=i))
                             for i in range(n_orders)])
    return client


def test_startup_sends_no_index_commands(run, commands):
    async def go():
        client = await init_db(URI, DB)
        await client.close()
    run(go())
    assert "createIndexes" not in commands.names() and "listIndexes" not in commands.names()


def test_index_job_creates_the_declared_indexes(run, commands):
    async def go():
        client = await fresh()
        info = await client[DB].orders.index_information()
        await client.close()
        return info
    assert "status_1_created_at_-1" in run(go())
    assert "createIndexes" in commands.names()


def test_recent_orders_is_two_commands(run, commands):
    async def go():
        client = await fresh()
        commands.sent.clear()
        rows = await recent_orders("paid", limit=50)
        await client.close()
        return rows
    rows = run(go())
    assert len(rows) == 50 and all(r["customer"] for r in rows)
    assert commands.names() == ["find", "find"]
    assert commands.sent[0][1]["sort"] == {"created_at": -1}


def test_fetch_link_per_order_is_n_plus_one(run, commands):
    async def go():
        client = await fresh()
        commands.sent.clear()
        orders = await Order.find(Order.status == "paid").sort(-Order.created_at).limit(50).to_list()
        for o in orders:
            await o.fetch_link(Order.customer)
        await client.close()
    run(go())
    assert len(commands.names()) == 51


def test_fetch_links_puts_lookup_before_sort_and_limit(run, commands):
    async def go():
        client = await fresh()
        commands.sent.clear()
        await Order.find(Order.status == "paid", fetch_links=True).sort(-Order.created_at).limit(5).to_list()
        await client.close()
    run(go())
    pipeline = commands.sent[0][1]["pipeline"]
    stages = [next(iter(s)) for s in pipeline]
    assert stages.index("$lookup") < stages.index("$sort") < stages.index("$limit")


def test_projection_model_asks_for_its_fields_only(run, commands):
    async def go():
        client = await fresh()
        commands.sent.clear()
        cards = await customer_cards("Paris")
        await client.close()
        return cards
    cards = run(go())
    assert cards and cards[0].email.endswith("@example.com")
    assert commands.sent[0][1]["projection"] == {"name": 1, "email": 1}


def test_patch_is_a_dotted_set_filtered_on_the_revision(run, commands):
    async def go():
        client = await fresh()
        c = await Customer.find_one(Customer.email == "c1@example.com")
        commands.sent.clear()
        await patch_customer(c, {"address.city": "Nice"})
        stored = await client[DB].customers.find_one({"_id": c.id})
        await client.close()
        return stored
    stored = run(go())
    name, cmd = commands.sent[0]
    assert name == "findAndModify"
    assert "revision_id" in cmd["query"]
    assert set(cmd["update"]["$set"]) == {"address.city", "revision_id"}
    assert stored["address"] == {"street": "1 Main St", "city": "Nice", "zip": "75001"}


def test_stale_patch_is_a_conflict(run):
    async def go():
        client = await fresh()
        a = await Customer.find_one(Customer.email == "c1@example.com")
        b = await Customer.find_one(Customer.email == "c1@example.com")
        await patch_customer(b, {"email": "new@example.com"})
        with pytest.raises(Conflict):
            await patch_customer(a, {"name": "Stale"})
        stored = await client[DB].customers.find_one({"_id": a.id})
        await client.close()
        return stored
    stored = run(go())
    assert (stored["name"], stored["email"]) == ("C1", "new@example.com")


def test_save_sends_every_field(run, commands):
    async def go():
        client = await fresh()
        c = await Customer.find_one(Customer.email == "c1@example.com")
        commands.sent.clear()
        c.loyalty_points = 5
        await c.save()
        await client.close()
    run(go())
    name, cmd = commands.sent[0]
    assert name == "findAndModify" and cmd["upsert"] is True
    assert {"name", "email", "address", "tags", "loyalty_points"} <= set(cmd["update"]["$set"])


def test_add_points_is_an_inc(run, commands):
    async def go():
        client = await fresh()
        c = await Customer.find_one(Customer.email == "c1@example.com")
        commands.sent.clear()
        await add_points(c, 7)
        await client.close()
    run(go())
    assert set(commands.sent[0][1]["update"]) == {"$inc", "$set"}  # $set: revision_id
    assert commands.sent[0][1]["update"]["$inc"] == {"loyalty_points": 7}
