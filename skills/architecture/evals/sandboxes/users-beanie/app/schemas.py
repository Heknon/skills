from beanie import PydanticObjectId
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+$")
    display_name: str = Field(min_length=1, max_length=60)
    password: str = Field(min_length=8)


class UserOut(BaseModel):
    id: PydanticObjectId
    email: str
    display_name: str
    bio: str
