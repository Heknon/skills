from pydantic import BaseModel
from pydantic_partial import PartialModelMixin


class User(PartialModelMixin, BaseModel):
    id: int
    name: str
    email: str | None = None


UserPatch = User.model_as_partial()
