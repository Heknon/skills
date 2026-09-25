import time


def pytest_addoption(parser):
    parser.addoption(
        "--no-tz-header", action="store_true", default=False,
        help="do not show the time zone in the header",
    )


def pytest_report_header(config):
    if config.getoption("no_tz_header"):
        return None
    return f"timezone: {time.tzname[0]}"
