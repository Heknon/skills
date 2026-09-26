"""Request models for the profiles API."""

from typing import Optional

from pydantic import BaseModel


class ProfileIn(BaseModel):
    """Body of POST /profiles.

    Contract agreed with the mobile team: `referrer` must always be sent,
    as null when there is none, so that old clients that forget it are
    caught. `nickname` may be left out.
    """

    username: str
    nickname: Optional[str]
    referrer: Optional[str]
