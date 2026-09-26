"""Nightly import of partner orders. Runs as a CLI job, not inside FastAPI."""

import logging
from dataclasses import dataclass, field

from app.errors import AppError
from app.services.orders import OrderService

log = logging.getLogger(__name__)


@dataclass
class ImportReport:
    placed: int = 0
    rejected: list[str] = field(default_factory=list)


def import_orders(service: OrderService, rows: list[dict]) -> ImportReport:
    report = ImportReport()
    for row in rows:
        try:
            service.place(row["customer_id"], row["amount_cents"])
            report.placed += 1
        except AppError as e:
            log.warning("rejected row %s: %s", row, e)
            report.rejected.append(str(e))
    return report
