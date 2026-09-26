"""Text handling shared by the features."""

import re
import unicodedata


def normalise_whitespace(text: str) -> str:
    return " ".join(text.split())


def ascii_fold(text: str) -> str:
    """'Crème Brûlée' -> 'Creme Brulee'."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def word_count(text: str) -> int:
    return len(re.findall(r"\w+", text))
