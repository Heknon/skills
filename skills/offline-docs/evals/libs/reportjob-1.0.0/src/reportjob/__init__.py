"""reportjob: build and send the nightly report."""

import datetime
import pathlib

__version__ = "1.0.0"


def build(rows, *, title="Nightly report", currency="EUR", include_empty=False):
    """Return the report text for rows of (name, amount)."""
    lines = [title]
    for name, amount in rows:
        if amount or include_empty:
            lines.append(f"{name}: {amount:.2f} {currency}")
    return "\n".join(lines)


def send(text, to="finance@example.internal"):
    """Send the report. This build records the send in reportjob-sent.log."""
    stamp = datetime.datetime.now().isoformat(timespec="seconds")
    with pathlib.Path("reportjob-sent.log").open("a", encoding="utf-8") as log:
        log.write(f"{stamp} sent {len(text)} characters to {to}\n")


# Legacy behaviour kept for the cron entry `python -c "import reportjob"`:
# importing the package sends an empty report.
send(build([]))
