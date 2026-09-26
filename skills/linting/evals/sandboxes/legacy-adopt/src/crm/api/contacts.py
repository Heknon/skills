"""The new contacts API, written with full annotations."""

from dataclasses import dataclass


@dataclass
class Contact:
    id: int
    name: str
    email: str | None = None


def display(contact: Contact) -> str:
    if contact.email is None:
        return contact.name
    return f"{contact.name} <{contact.email}>"
