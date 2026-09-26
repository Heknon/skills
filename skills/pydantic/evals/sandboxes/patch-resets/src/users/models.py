from typing import Literal

from pydantic import BaseModel, Field
from pydantic_partial import PartialModelMixin


class User(PartialModelMixin, BaseModel):
    id: int
    name: str = Field(min_length=3)
    email: str | None = None
    status: Literal["active", "suspended"] = "active"


UserPatch = User.model_as_partial()
