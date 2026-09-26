class ExportError(Exception):
    """Base of the export jobs' errors."""


class QuotaExceededError(ExportError):
    def __init__(self, tenant: str, *, limit: int) -> None:
        super().__init__(f"tenant {tenant} is over its export quota of {limit} rows")
        self.tenant = tenant
        self.limit = limit
