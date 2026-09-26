"""Notes on orders, and the audit trail. In memory for this service."""

from dataclasses import dataclass, field


@dataclass
class NoteStore:
    notes: dict[str, list[str]] = field(default_factory=dict)

    def add(self, order_id: str, text: str) -> None:
        self.notes.setdefault(order_id, []).append(text)


@dataclass
class AuditLog:
    lines: list[str] = field(default_factory=list)

    def record(self, line: str) -> None:
        self.lines.append(line)


STORE = NoteStore()
AUDIT = AuditLog()
