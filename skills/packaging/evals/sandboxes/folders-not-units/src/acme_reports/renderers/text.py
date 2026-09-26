from acme_reports.store.models import Row


def render(rows: list[Row]) -> str:
    return "\n".join(f"{r.region:<6}{r.amount:>10.2f}" for r in rows)
