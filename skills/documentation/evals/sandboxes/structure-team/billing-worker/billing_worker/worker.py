import json
import urllib.request

LEDGER_URL = "http://ledger.internal/entries"


def handle(message):
    entry = {"customer": message["customer"], "amount": message["amount"], "kind": "charge"}
    request = urllib.request.Request(LEDGER_URL, data=json.dumps(entry).encode(), method="POST")
    urllib.request.urlopen(request, timeout=10)


def main():
    subscribe("charges.created", handle)


def subscribe(topic, handler):
    print("subscribed", topic, handler.__name__)
