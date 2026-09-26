from vouchers.api import create_voucher


def test_code_is_normalised():
    status, body = create_voucher({"code": " spring10 ", "percent": 10})
    assert status == 201
    assert body["code"] == "SPRING10"


def test_missing_percent_is_422():
    status, _ = create_voucher({"code": "x"})
    assert status == 422
