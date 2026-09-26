import json


def load_items(path):
    """Read a supplier feed: a JSON object with an "items" list."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)["items"]
