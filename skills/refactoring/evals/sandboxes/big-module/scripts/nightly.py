"""Nightly job: print the report for the demo orders."""

from app.cli import demo_orders
from app.reports import render_text

if __name__ == "__main__":
    print(render_text(demo_orders(), title="Nightly"))
