from app.articles.service import create_article
from app.tags.service import create_tag
from app.text import ascii_fold


def test_article():
    a = create_article("  Hello   World ", "one two three")
    assert (a.title, a.words) == ("Hello World", 3)


def test_tag():
    assert create_tag("  Python  Tips ").name == "python tips"


def test_ascii_fold():
    assert ascii_fold("Crème Brûlée") == "Creme Brulee"
