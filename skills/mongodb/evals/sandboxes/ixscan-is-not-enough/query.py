"""Open orders for the regional report (runs every few minutes)."""


def big_open_orders(db, country: str, city: str):
    return list(
        db.orders.find(
            {
                "status": {"$ne": "shipped"},
                "country": country,
                "address.city": city,
                "total_cents": {"$gte": 200_000},
            }
        )
    )
