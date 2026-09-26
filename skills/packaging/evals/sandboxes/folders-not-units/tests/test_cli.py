from click.testing import CliRunner

from acme_reports.cli import main


def test_report(tmp_path):
    f = tmp_path / "sales.csv"
    f.write_text("region,amount\nnorth,12.5\n")
    assert CliRunner().invoke(main, [str(f)]).output == "north      12.50\n"
