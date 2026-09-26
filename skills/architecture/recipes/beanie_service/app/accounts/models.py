"""The stored document. Only repository.py uses this class."""

from beanie import Document
from pymongo import IndexModel


class AccountDocument(Document):
    owner_email: str
    kyc_reference: str
    balance_cents: int = 0

    class Settings:
        name = "accounts"
        indexes = [IndexModel("owner_email", name="owner_email_1", unique=True)]
