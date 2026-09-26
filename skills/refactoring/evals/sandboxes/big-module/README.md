# app

`app/reports.py` holds money formatting, order totals, the CSV export and
the text report. It is imported as `app.reports` by the web layer
(`app/api.py`), the CLI (`app/cli.py`), the nightly script
(`scripts/nightly.py`) and by other teams' services, which pin this
package and import `from app.reports import ...`.
