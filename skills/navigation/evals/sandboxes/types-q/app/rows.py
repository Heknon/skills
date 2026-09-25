import csv


def parse_rows(lines):
    reader = csv.reader(lines)
    header = next(reader)
    return [dict(zip(header, row)) for row in reader]
