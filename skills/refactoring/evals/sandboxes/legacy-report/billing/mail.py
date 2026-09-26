"""Morning mail: uv run python -m billing.mail data/invoices.csv"""

import sys

from billing.report import build_report

if __name__ == "__main__":
    print(build_report(sys.argv[1]))
