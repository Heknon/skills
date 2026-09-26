from typing import Union

from pydantic import BaseModel


class Dog(BaseModel):
    type: str
    name: str
    breed: str = "unknown"


class Cat(BaseModel):
    type: str
    name: str
    indoor: bool = True


class Owner(BaseModel):
    name: str
    pets: list[Union[Dog, Cat]]
