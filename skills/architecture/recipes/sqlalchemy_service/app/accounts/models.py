"""The table. Only repository.py uses this class."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AccountRow(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_email: Mapped[str] = mapped_column(String(254), unique=True)
    kyc_reference: Mapped[str] = mapped_column(String(64))
    balance_cents: Mapped[int] = mapped_column(default=0)
