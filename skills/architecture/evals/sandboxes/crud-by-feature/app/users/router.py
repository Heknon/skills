from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.db import Database, get_db
from app.users import crud
from app.users.schemas import UserCreate, UserOut

router = APIRouter(prefix="/users", tags=["users"])
DbDep = Annotated[Database, Depends(get_db)]


@router.post("", status_code=201)
def create_user(body: UserCreate, db: DbDep) -> UserOut:
    return UserOut.model_validate(crud.create_user(db, body.email, body.name))


@router.get("/{user_id}")
def get_user(user_id: int, db: DbDep) -> UserOut:
    row = crud.get_user(db, user_id)
    if row is None:
        raise HTTPException(404, f"user {user_id} not found")
    return UserOut.model_validate(row)
