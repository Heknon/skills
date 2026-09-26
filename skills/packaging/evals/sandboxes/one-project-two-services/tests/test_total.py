from click.testing import CliRunner

from acme_api.cli import main as api_main
from acme_worker.cli import main as worker_main


def test_api():
    assert CliRunner().invoke(api_main, ["1.10", "2.20"]).output == "order total 3.30\n"


def test_worker():
    assert CliRunner().invoke(worker_main, ["1.10", "2.20"]).output == "batch total 3.30\n"
