from pathlib import Path

from names.load import load_names

DATA = Path(__file__).parent.parent / "data" / "customers.txt"


def test_load_names():
    names = load_names(DATA)
    assert names[0] == "Álvaro Núñez"
    assert len(names) == 4
