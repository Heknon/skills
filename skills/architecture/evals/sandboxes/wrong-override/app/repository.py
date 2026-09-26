import json
import os
from pathlib import Path


class NoteRepository:
    """Notes stored as JSON files in a shared folder (NOTES_DIR)."""

    def __init__(self, folder: Path) -> None:
        self.folder = folder

    def get(self, note_id: int) -> dict | None:
        path = self.folder / f"{note_id}.json"
        return json.loads(path.read_text()) if path.exists() else None


def get_repo() -> NoteRepository:
    return NoteRepository(Path(os.environ.get("NOTES_DIR", "/srv/notes")))
