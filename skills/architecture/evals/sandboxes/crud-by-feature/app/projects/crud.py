"""Database access for projects. One function per operation; no HTTP here."""

from app.db import Database, ProjectRow


def create_project(db: Database, name: str, owner_id: int) -> ProjectRow:
    row = ProjectRow(id=db.new_id(), name=name, owner_id=owner_id)
    db.projects[row.id] = row
    return row


def get_project(db: Database, project_id: int) -> ProjectRow | None:
    return db.projects.get(project_id)


def list_projects(db: Database) -> list[ProjectRow]:
    return sorted(db.projects.values(), key=lambda p: p.id)
