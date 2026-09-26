from collections.abc import Iterable


def header(rows: Iterable[list[str]]) -> list[str]:
    """Return the first row of a CSV file.

    Raises IndexError when the file has no rows; load() relies on that.
    """
    return list(rows)[0]


def load(rows: Iterable[list[str]]) -> dict[str, list[list[str]]]:
    try:
        columns = header(rows)
    except IndexError:
        return {"columns": [], "rows": []}
    return {"columns": columns, "rows": []}
