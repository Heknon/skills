from dataclasses import dataclass


@dataclass
class Note:
    id: int
    title: str
    body: str


class NoteStore:
    def __init__(self) -> None:
        self._notes: dict[int, Note] = {}

    def add(self, title: str, body: str) -> Note:
        note = Note(id=len(self._notes) + 1, title=title, body=body)
        self._notes[note.id] = note
        return note

    def get(self, note_id: int) -> Note | None:
        return self._notes.get(note_id)
