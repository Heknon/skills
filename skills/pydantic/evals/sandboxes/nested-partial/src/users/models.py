from pydantic import BaseModel
from pydantic_partial import PartialModelMixin


class Address(BaseModel):
    street: str
    city: str
    postcode: str


class User(PartialModelMixin, BaseModel):
    id: int
    name: str
    address: Address


UserPatch = User.model_as_partial(recursive=True)
