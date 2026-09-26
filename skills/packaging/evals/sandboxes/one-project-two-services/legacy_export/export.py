import csv
import io


def rows_to_csv(rows: list[dict[str, str]]) -> str:
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=sorted(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()
