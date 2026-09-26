from dataclasses import dataclass

from app.text import normalise_whitespace, word_count
from app.utils import truncate


@dataclass
class Article:
    title: str
    body: str
    summary: str
    words: int


def create_article(title: str, body: str) -> Article:
    title = normalise_whitespace(title)
    return Article(title=title, body=body, summary=truncate(body, 140), words=word_count(body))
