from shop import Client


def sync_orders(base_url):
    client = Client(base_url)
    return client.get("/orders")
