import configparser
import json
import os
import tomllib
from pathlib import Path


class UnsupportedFormat(ValueError):
    pass


def _read_toml(text):
    return tomllib.loads(text)


def _read_json(text):
    return json.loads(text)


def _read_ini(text):
    parser = configparser.ConfigParser()
    parser.read_string(text)
    return {name: dict(parser[name]) for name in parser.sections()}


_READERS = {"toml": _read_toml, "json": _read_json, "ini": _read_ini}
_SUFFIXES = {".toml": "toml", ".json": "json", ".ini": "ini", ".cfg": "ini"}


def load(path, *, format="auto", env_prefix=None, defaults=None):
    """Read settings from path, then override them from the environment.

    format: "auto" (from the file suffix) or one of the known formats.
    env_prefix: if given, variables named PREFIX_KEY override KEY.
    """
    path = Path(path)
    if format == "auto":
        format = _SUFFIXES.get(path.suffix.lower(), path.suffix)
    try:
        reader = _READERS[format]
    except KeyError:
        known = ", ".join(sorted(_READERS))
        raise UnsupportedFormat(f"cannot read {format!r}; known formats: {known}") from None
    data = dict(defaults or {})
    data.update(reader(path.read_text(encoding="utf-8")))
    if env_prefix:
        start = env_prefix.upper() + "_"
        for name, value in os.environ.items():
            if name.startswith(start):
                data[name[len(start):].lower()] = value
    return data
