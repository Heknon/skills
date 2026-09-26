import httpx


class LedgerClient:
    def __init__(self, base_url: str, token: str) -> None:
        self._http = httpx.Client(base_url=base_url, headers={"Authorization": f"Bearer {token}"})

    def balance(self, account: str) -> float:
        response = self._http.get(f"/accounts/{account}/balance")
        response.raise_for_status()
        return float(response.json()["balance"])
