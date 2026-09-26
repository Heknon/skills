from pydantic import BaseModel, field_validator
from pydantic_partial import PartialModelMixin


class User(PartialModelMixin, BaseModel):
    id: int
    name: str
    email: str | None = None

    @field_validator("name")
    @classmethod
    def tidy_name(cls, v: str) -> str:
        return " ".join(v.strip().split()).title()


UserPatch = User.model_as_partial()
