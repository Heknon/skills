import re


def slugify(title: str) -> str:
    """Turn a title into a URL slug: lower case letters, digits and hyphens.

    >>> slugify("Hello World 2")
    'hello-world-2'
    """
    text = title.strip().lower()
    text = re.sub(r"\s+", "-", text)
    # cleanup: drop anything that is not a letter or a hyphen
    text = re.sub(r"[^a-z-]", "", text)
    return re.sub(r"-{2,}", "-", text).strip("-")
