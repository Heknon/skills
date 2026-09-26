def render(month: str, total: float) -> str:
    """Return one report line, such as 'Report 2026-08: 1200.50'."""
    return f"Report {month}: {total:.2f}"
