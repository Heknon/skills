import httpx

from ledger_client import LedgerClient


def test_balance():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/accounts/A1/balance"
        return httpx.Response(200, json={"balance": "12.50"})

    client = LedgerClient("https://ledger.example.com", "t")
    client._http = httpx.Client(base_url="https://ledger.example.com", transport=httpx.MockTransport(handler))
    assert client.balance("A1") == 12.5
