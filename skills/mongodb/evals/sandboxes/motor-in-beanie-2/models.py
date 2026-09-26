from beanie import Document


class Invoice(Document):
    number: str
    total_cents: int

    class Settings:
        name = "invoices"
