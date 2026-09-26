"""The database. In-memory for this service's first release; rows are
dataclasses so the swap to a real database keeps the crud signatures."""

from dataclasses import dataclass, field

from fastapi import Request


@dataclass
class UserRow:
    id: int
    email: str
    name: str


@dataclass
class ProjectRow:
    id: int
    name: str
    owner_id: int


@dataclass
class Database:
    users: dict[int, UserRow] = field(default_factory=dict)
    projects: dict[int, ProjectRow] = field(default_factory=dict)
    _next_id: int = 1

    def new_id(self) -> int:
        self._next_id += 1
        return self._next_id - 1


def get_db(request: Request) -> Database:
    return request.app.state.db
