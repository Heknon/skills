import json

DEFAULT_PATH = "config/app.json"


def load_settings(path=DEFAULT_PATH):
    with open(path) as handle:
        return json.load(handle)
