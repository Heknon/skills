"""Customer lookup."""

from dataclasses import dataclass


class CustomerNotFound(LookupError):
    """No customer has this email."""

    def __init__(self, email: str) -> None:
        super().__init__(email)
        self.email = email


@dataclass(frozen=True)
class Customer:
    email: str
    name: str


_CUSTOMERS = {
    "ann@example.com": Customer("ann@example.com", "Ann Lee"),
    "bob@example.com": Customer("bob@example.com", "Bob Stone"),
}


def find_customer(email: str) -> Customer:
    """The customer with this email, in any case; CustomerNotFound if none."""
    key = email.strip().lower()
    try:
        return _CUSTOMERS[key]
    except KeyError:
        raise CustomerNotFound(email) from None
