from app.errors import QuotaExceededError

QUOTAS = {"acme": 100, "globex": 10_000}


def export_rows(tenant: str, rows: int) -> str:
    limit = QUOTAS[tenant]
    if rows > limit:
        raise QuotaExceededError(tenant, limit=limit)
    return f"exported {rows} rows for {tenant}"
