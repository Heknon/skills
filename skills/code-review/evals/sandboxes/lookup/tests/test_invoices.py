from shop.invoices import invoice_header


def test_invoice_header_names_the_customer() -> None:
    assert invoice_header("bob@example.com", 7) == "Invoice 7 - Bob Stone"
