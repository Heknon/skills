from click.testing import CliRunner

from report.cli import main


def test_prints_report_line():
    result = CliRunner().invoke(main, ["2026-08", "--total", "1200.5"])
    assert result.exit_code == 0
    assert result.output == "Report 2026-08: 1200.50\n"
