import sys
import tomllib

from reports.client import ReportServiceError, fetch_report


def main():
    with open("settings.toml", "rb") as f:
        settings = tomllib.load(f)
    try:
        report = fetch_report(settings["base_url"], settings["api_token"], "daily-sales")
    except ReportServiceError as exc:
        print(f"nightly report failed: {exc}", file=sys.stderr)
        return 2
    print(f"{len(report['rows'])} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
