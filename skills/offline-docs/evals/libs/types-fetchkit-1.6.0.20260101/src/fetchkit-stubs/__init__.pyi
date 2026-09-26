__version__: str

def get(
    url: str,
    *,
    query: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    retries: int = 0,
) -> bytes: ...
def post(
    url: str,
    body: bytes,
    *,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    retries: int = 0,
) -> bytes: ...
