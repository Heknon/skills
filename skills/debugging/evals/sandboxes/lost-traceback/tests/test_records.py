from crm.records import clean


def test_clean():
    record = {"name": " Ana ", "email": "Ana@Example.com ", "phone": None, "company": None, "country": "gb"}
    assert clean(record) == {
        "name": "Ana",
        "email": "ana@example.com",
        "phone": "",
        "company": "",
        "country": "United Kingdom",
    }
