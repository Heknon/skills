from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()


class UserIn(BaseModel):
    name: str = Field(min_length=1)
    email: str
    locale: str = "en"
    newsletter: bool = False


class User(UserIn):
    id: int


USERS: dict[int, User] = {
    1: User(id=1, name="Ann", email="ann@example.com", locale="fr", newsletter=True),
}


@app.get("/users/{user_id}")
def get_user(user_id: int) -> User:
    if user_id not in USERS:
        raise HTTPException(status_code=404, detail="User not found")
    return USERS[user_id]


@app.post("/users", status_code=201)
def create_user(body: UserIn) -> User:
    user = User(id=max(USERS) + 1, **body.model_dump())
    USERS[user.id] = user
    return user
