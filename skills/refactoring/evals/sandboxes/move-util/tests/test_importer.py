from app.importer import normalise


def test_normalise_weekday():
    assert normalise("Ada Lovelace;2026-03-02") == "ada-lovelace;2026-03-02"


def test_normalise_weekend():
    assert normalise("Ada;01/03/2026") == "ada;2026-03-01 (weekend)"
