import json
import os
from typing import List, Optional

MONTHLY_TOTALS_QUERY = "SELECT account_id, date_trunc('month', booked_at) AS month, sum(amount_cents) AS total FROM ledger_entries GROUP BY 1, 2 ORDER BY 1, 2"


def monthly_rows(rows: List[dict], currency: Optional[str] = None) -> list[dict]:
    result = []
    skipped = 0
    for row in rows:
        result.append({"account": row["account_id"], "month": row["month"], "total": row["total"], "currency": currency or "EUR"})
    return result


def to_json(rows: list[dict]) -> str:
    return json.dumps(rows)
