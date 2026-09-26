from pathlib import Path

from sales.parser import read_rows
from sales.report import totals_by_region

DATA = Path(__file__).parent.parent / "data"


def test_totals_by_region():
    rows = [
        {"region": "North", "amount": 10.0},
        {"region": "North", "amount": 5.0},
        {"region": "South", "amount": 1.0},
    ]
    assert totals_by_region(rows) == {"North": 15.0, "South": 1.0}


def test_april_export():
    assert totals_by_region(read_rows(DATA / "april.csv")) == {"North": 140.0, "South": 80.0}
