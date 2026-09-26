from dataclasses import dataclass

from app.text import normalise_whitespace


@dataclass
class Tag:
    name: str


def create_tag(name: str) -> Tag:
    return Tag(name=normalise_whitespace(name).lower())
