from invoicer.cli import render


def test_total_is_filled_in():
    assert "Total: 42.00" in render("42.00")
