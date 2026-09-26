from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    """A user as the identity service sends it: camelCase on the wire."""

    model_config = ConfigDict(validate_by_name=True)

    id: int
    display_name: str = Field(alias="displayName")
    email: str
