"""Response bodies of the public users API (served as JSON to the mobile app and partners)."""

from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    user_name: str
    display_name: str
    email: str
