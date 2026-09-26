from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.db import Database, get_db
from app.projects import crud
from app.projects.schemas import ProjectCreate, ProjectOut
from app.users import crud as users_crud

router = APIRouter(prefix="/projects", tags=["projects"])
DbDep = Annotated[Database, Depends(get_db)]


@router.post("", status_code=201)
def create_project(body: ProjectCreate, db: DbDep) -> ProjectOut:
    if users_crud.get_user(db, body.owner_id) is None:
        raise HTTPException(422, f"owner {body.owner_id} does not exist")
    return ProjectOut.model_validate(crud.create_project(db, body.name, body.owner_id))


@router.get("")
def list_projects(db: DbDep) -> list[ProjectOut]:
    return [ProjectOut.model_validate(p) for p in crud.list_projects(db)]


@router.get("/{project_id}")
def get_project(project_id: int, db: DbDep) -> ProjectOut:
    row = crud.get_project(db, project_id)
    if row is None:
        raise HTTPException(404, f"project {project_id} not found")
    return ProjectOut.model_validate(row)
