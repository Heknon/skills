from textkit.slug import slugify


def test_slugify_lowercases_and_joins():
    assert slugify("Hello World") == "hello-world"


def test_slugify_drops_punctuation():
    assert slugify("Rock & Roll!") == "rock-roll"


def test_slugify_keeps_digits():
    assert slugify("Release 2 notes") == "release-2-notes"
