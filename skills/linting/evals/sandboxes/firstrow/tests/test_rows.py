import pytest

from importer.rows import header, load


def test_header() -> None:
    assert header([["a", "b"], ["1", "2"]]) == ["a", "b"]


def test_empty_file_raises_index_error() -> None:
    with pytest.raises(IndexError):
        header([])


def test_load_empty_file() -> None:
    assert load([]) == {"columns": [], "rows": []}
