# L7: imports point up, or round

**Rule.** Imports point one way, from the edge inwards: router ->
schemas and service -> repository -> database models -> domain ->
errors. A lower module never imports a higher one, and two modules
never import each other. A function-level import that exists only to
break a cycle is the same violation, hidden.

**Why.** *lab,* sandbox circular: `models.py` imported `schemas.py` for
a `to_out()` mapper while `schemas.py` imported `models.py`; the app did
not start: `ImportError: cannot import name 'Member' from partially
initialized module 'app.models' (most likely due to a circular import)`.
Moving the import into `to_out()` made it start, and ruff's `PLC0415`
(`import` should be at the top-level of a file) flagged the hidden
cycle.

**Target.** The mapping moves to the higher side (the schema gets a
`from_member` classmethod, or the router maps), and the lower module
loses the import.

## Before

```python file=before/app/models.py
from dataclasses import dataclass


@dataclass
class Member:
    id: int
    name: str
    password_hash: str

    def to_out(self):
        from app.schemas import MemberOut   # hides models -> schemas -> models

        return MemberOut(id=self.id, name=self.name)
```

```python file=before/app/schemas.py
from pydantic import BaseModel

from app.models import Member


class MemberIn(BaseModel):
    name: str

    def to_member(self, member_id: int) -> Member:
        return Member(id=member_id, name=self.name, password_hash="")


class MemberOut(BaseModel):
    id: int
    name: str
```

```python file=before/app/main.py
from app.schemas import MemberIn


def create(name: str):
    return MemberIn(name=name).to_member(1).to_out()
```

## After

```python file=after/app/models.py
from dataclasses import dataclass


@dataclass
class Member:
    id: int
    name: str
    password_hash: str
```

```python file=after/app/schemas.py
from pydantic import BaseModel

from app.models import Member


class MemberIn(BaseModel):
    name: str

    def to_member(self, member_id: int) -> Member:
        return Member(id=member_id, name=self.name, password_hash="")


class MemberOut(BaseModel):
    id: int
    name: str

    @classmethod
    def from_member(cls, member: Member) -> "MemberOut":
        return cls(id=member.id, name=member.name)
```

```python file=after/app/main.py
from app.schemas import MemberIn, MemberOut


def create(name: str):
    return MemberOut.from_member(MemberIn(name=name).to_member(1))
```

## The test both pass

```python file=test_shape.py
from app.main import create


def test_create_maps_to_the_public_shape():
    assert create("Ada").model_dump() == {"id": 1, "name": "Ada"}
```

After only: the lower module imports nothing from the higher one.

```python file=after/test_direction.py
import ast
import pathlib


def test_models_import_no_schemas():
    tree = ast.parse(pathlib.Path("app/models.py").read_text())
    names = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    assert "app.schemas" not in names
```

Checked with `uv run python check_shapes.py L7`; the after-only test
fails on the before (it finds the function-level import). Steps:
refactoring's recipe `L7`.
