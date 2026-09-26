"""Domain models: what the service works with."""

from dataclasses import dataclass

from app.schemas import MemberOut


@dataclass
class Member:
    id: int
    email: str
    name: str
    password_hash: str

    def to_out(self) -> MemberOut:
        return MemberOut(id=self.id, name=self.name)
