_FAKE = {
    "/products": [{"sku": "a-1", "net": "10.00"}, {"sku": "b-2", "net": "2.50"}],
}


def get(path, params):
    if path.startswith("/stock/"):
        return {"available": True}
    return _FAKE.get(path, [])
