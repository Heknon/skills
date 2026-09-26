"""Loyalty points."""

from dataclasses import dataclass


@dataclass
class Account:
    id: str
    balance: int


class InsufficientPoints(Exception):
    """The account holds fewer points than asked for."""

    def __init__(self, account_id: str) -> None:
        super().__init__(account_id)
        self.account_id = account_id


AUDIT: list[str] = []


def audit(line: str) -> None:
    AUDIT.append(line)
