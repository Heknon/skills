from legacy_utils import slugify


def article_url(title: str) -> str:
    return "/articles/" + slugify(title)
