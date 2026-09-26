"""Request and response bodies."""

from pydantic import BaseModel

from app.models import Member


class MemberIn(BaseModel):
    email: str
    name: str
    password: str

    def to_member(self, member_id: int, password_hash: str) -> Member:
        return Member(id=member_id, email=self.email, name=self.name, password_hash=password_hash)


class MemberOut(BaseModel):
    id: int
    name: str
