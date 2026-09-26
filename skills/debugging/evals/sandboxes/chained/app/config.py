import json
import sys


class ConfigError(Exception):
    pass


def load(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        print(f"{path}: syntax error on line {exc.line}", file=sys.stderr)
        raise ConfigError(f"cannot read {path}")
