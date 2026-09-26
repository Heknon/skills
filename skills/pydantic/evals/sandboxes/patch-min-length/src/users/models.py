from pydantic import BaseModel, Field
from pydantic_partial import PartialModelMixin


class User(PartialModelMixin, BaseModel):
    id: int
    name: str = Field(min_length=3, max_length=40)
    email: str | None = None


UserPatch = User.model_as_partial()
