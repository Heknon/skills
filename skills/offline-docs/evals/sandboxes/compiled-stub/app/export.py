import orjson


def export_report(report: dict) -> bytes:
    return orjson.dumps(report)
