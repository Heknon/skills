"""Show which source set each field of a pydantic-settings class.

Copy this file anywhere and run it from the folder the service is started
from (relative paths such as env_file=".env" are resolved from there):

    uv run --no-sync python trace_settings.py <module>:<Class>
    uv run --no-sync python trace_settings.py api.config:Settings

With a src layout that is not installed, add the folder to the path for
that one run (PowerShell):

    $env:PYTHONPATH = "src"; uv run --no-sync python trace_settings.py api.config:Settings; Remove-Item Env:PYTHONPATH

It builds the class's own sources, in the order its
settings_customise_sources returns them (highest priority first), calls
each source alone, and prints for every field the source that wins and
every other source that also set it. Secret values are never printed:
SecretStr and SecretBytes fields, and fields whose name contains one of
SECRET_WORDS, are shown as <secret, N chars>. It reads, it changes
nothing. Verified on pydantic-settings 2.15.0 and 2.12.0.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, SecretBytes, SecretStr, ValidationError
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    EnvSettingsSource,
    InitSettingsSource,
    SecretsSettingsSource,
)

SECRET_WORDS = ("password", "secret", "token", "key", "credential", "dsn", "url")


def load_class(target: str) -> type[BaseSettings]:
    module_name, _, class_name = target.partition(":")
    if not class_name:
        sys.exit("usage: trace_settings.py <module>:<Class>")
    cls = getattr(importlib.import_module(module_name), class_name)
    if not (isinstance(cls, type) and issubclass(cls, BaseSettings)):
        sys.exit(f"{target} is not a BaseSettings subclass")
    return cls


def is_secret(cls: type[BaseModel], path: str) -> bool:
    """True if any part of a dotted path names, or is typed as, a secret."""
    model: Any = cls
    for part in path.split("."):
        text = part.lower()
        field = getattr(model, "model_fields", {}).get(part)
        if field is not None:
            text += f" {field.annotation}".lower()
        if any(w in text for w in SECRET_WORDS) or "secret" in text:
            return True
        model = field.annotation if field is not None else None
    return False


def alias_map(cls: type[BaseSettings]) -> dict[str, str]:
    """Sources return a field set through an alias under the alias."""
    names: dict[str, str] = {}
    for name, field in cls.model_fields.items():
        names[name] = name
        aliases = [field.alias, field.validation_alias]
        choices = getattr(field.validation_alias, "choices", None)
        if choices:
            aliases.extend(choices)
        for alias in aliases:
            if isinstance(alias, str):
                names[alias] = name
                names[alias.lower()] = name
    return names


def show(value: Any, secret: bool) -> str:
    if isinstance(value, (SecretStr, SecretBytes)):
        value = value.get_secret_value()
        secret = True
    if secret:
        return f"<secret, {len(str(value))} chars>"
    return repr(value)


def flatten(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in data.items():
        path = f"{prefix}{key}"
        if isinstance(value, dict) and value:
            out.update(flatten(value, path + "."))
        else:
            out[path] = value
    return out


def build_sources(cls: type[BaseSettings]) -> list[Any]:
    # The same four built-in sources BaseSettings creates, each reading the
    # class's model_config, passed through the class's own hook.
    return list(
        cls.settings_customise_sources(
            cls,
            init_settings=InitSettingsSource(cls, init_kwargs={}),
            env_settings=EnvSettingsSource(cls),
            dotenv_settings=DotEnvSettingsSource(cls),
            file_secret_settings=SecretsSettingsSource(cls),
        )
    )


def describe(source: Any) -> str:
    name = type(source).__name__
    if isinstance(source, DotEnvSettingsSource):
        files = source.env_file
        if files is None:
            return f"{name} (env_file not set)"
        files = [files] if isinstance(files, (str, Path)) else list(files)
        shown = ", ".join(
            f"{Path(f).expanduser().resolve()} ({'found' if Path(f).expanduser().is_file() else 'NOT FOUND'})"
            for f in files
        )
        return f"{name} {shown}"
    if isinstance(source, SecretsSettingsSource):
        dirs = source.secrets_dir
        if dirs is None:
            return f"{name} (secrets_dir not set)"
        dirs = [dirs] if isinstance(dirs, (str, Path)) else list(dirs)
        shown = ", ".join(
            f"{Path(d).expanduser().resolve()} ({'found' if Path(d).expanduser().is_dir() else 'NOT FOUND'})"
            for d in dirs
        )
        return f"{name} {shown}"
    if isinstance(source, EnvSettingsSource):
        return f"{name} (process environment)"
    return name


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: trace_settings.py <module>:<Class>")
    sys.path.insert(0, str(Path.cwd()))
    cls = load_class(sys.argv[1])
    names = alias_map(cls)
    config = cls.model_config
    print(f"class:      {cls.__module__}.{cls.__qualname__}")
    print(f"cwd:        {Path.cwd()}")
    print(f"env_prefix: {config.get('env_prefix')!r}  case_sensitive: {config.get('case_sensitive')}  "
          f"nested_delimiter: {config.get('env_nested_delimiter')!r}  extra: {config.get('extra')!r}")

    sources = build_sources(cls)
    print("sources, highest priority first:")
    per_source: list[tuple[str, dict[str, Any]]] = []
    for i, source in enumerate(sources, 1):
        label = type(source).__name__
        print(f"  {i}. {describe(source)}")
        try:
            data = source()
            data = {names.get(k, k): v for k, v in data.items()}
            per_source.append((label, flatten(data)))
        except Exception as exc:  # a broken source is a finding, not a crash
            print(f"     ERROR reading it: {type(exc).__name__}: {exc}")
            per_source.append((label, {}))

    defaults = {}
    for name, field in cls.model_fields.items():
        if not field.is_required():
            defaults[name] = field.get_default(call_default_factory=True)
    per_source.append(("default", flatten({k: v.model_dump() if hasattr(v, "model_dump") else v
                                           for k, v in defaults.items()})))

    fields = list(cls.model_fields)
    print("\nper field (the first line wins):")
    for name in fields:
        hits = [(label, key, value) for label, data in per_source for key, value in data.items()
                if key == name or key.startswith(name + ".")]
        if not hits:
            print(f"  {name}: set by no source (required, so building the class fails)")
            continue
        keys = sorted({key for _, key, _ in hits}, key=lambda k: (k.count("."), k))
        for key in keys:
            secret = is_secret(cls, key)
            rows = [(label, value) for label, k, value in hits if k == key]
            winner, value = rows[0]
            print(f"  {key} = {show(value, secret)}   <- {winner}")
            for label, other in rows[1:]:
                print(f"      also set by {label}: {show(other, secret)}")

    extras = [(label, key) for label, data in per_source for key in data if key.split(".")[0] not in fields]
    if extras:
        print("\nkeys that match no field (extra):")
        for label, key in extras:
            print(f"  {key}   from {label}   (extra={config.get('extra')!r})")

    print("\nbuilding the class:")
    try:
        cls()
        print("  ok")
    except ValidationError as exc:
        # errors without their input: an input may be a secret
        print(f"  FAILED: {exc.error_count()} validation error(s)")
        for err in exc.errors(include_input=False, include_url=False):
            loc = ".".join(str(p) for p in err["loc"])
            print(f"    {loc}: {err['type']} ({err['msg']})")
    except Exception as exc:
        print(f"  FAILED: {type(exc).__name__}: {str(exc).splitlines()[0]}")


if __name__ == "__main__":
    main()
