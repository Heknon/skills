"""Client for the separate admin directory. Not the same users as app.users."""


class AdminClient:
    def __init__(self, directory: dict[str, str]) -> None:
        self._directory = directory

    def get_user(self, login: str) -> str | None:
        """Return the admin's display name for a login, or None."""
        return self._directory.get(login)
