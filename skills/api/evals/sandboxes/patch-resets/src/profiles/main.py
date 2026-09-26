from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()


class Profile(BaseModel):
    id: int
    display_name: str = Field(min_length=1, max_length=40)
    bio: str | None = None


class ProfileUpdate(BaseModel):
    display_name: str | None = None
    bio: str | None = None


PROFILES: dict[int, Profile] = {
    1: Profile(id=1, display_name="Ann", bio="Cyclist"),
}


@app.get("/profiles/{profile_id}")
def get_profile(profile_id: int) -> Profile:
    if profile_id not in PROFILES:
        raise HTTPException(status_code=404, detail="Profile not found")
    return PROFILES[profile_id]


@app.patch("/profiles/{profile_id}")
def update_profile(profile_id: int, body: ProfileUpdate) -> Profile:
    if profile_id not in PROFILES:
        raise HTTPException(status_code=404, detail="Profile not found")
    stored = PROFILES[profile_id]
    PROFILES[profile_id] = stored.model_copy(update=body.model_dump())
    return PROFILES[profile_id]
