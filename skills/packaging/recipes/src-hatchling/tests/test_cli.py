from click.testing import CliRunner

from acme_report.cli import main


def test_report_line():
    result = CliRunner().invoke(main, ["2026-08", "--total", "1200.5"])
    assert result.exit_code == 0
    assert result.output == "Report 2026-08: 1200.50\n"
