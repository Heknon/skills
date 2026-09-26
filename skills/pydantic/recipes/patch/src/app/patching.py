"""Apply a PATCH body to a stored model, the pydantic part of the flow.

1. parse the body with the partial model          (shape and types)
2. merge what the body set onto the stored model  (unset stays, null clears)
3. validate the merged result with the full model (constraints, validators,
                                                    rules across fields)
The caller stores `changes`, which holds only what the body set, with the
values the full model produced (a validator may have changed them).
Turning `changes` into a database update is the store's job.
"""

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

M = TypeVar("M", bound=BaseModel)


@dataclass(frozen=True)
class Patched(Generic[M]):
    model: M                  # the full model after the patch, validated
    changes: dict[str, Any]   # nested dict: only the paths the body set


def deep_merge(base: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
    """Nested dicts merge key by key; anything else, lists too, replaces."""
    merged = dict(base)
    for key, value in changes.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def pick(values: dict[str, Any], shape: dict[str, Any]) -> dict[str, Any]:
    """The parts of `values` at the paths present in `shape`."""
    out: dict[str, Any] = {}
    for key, sub in shape.items():
        if isinstance(sub, dict) and isinstance(values.get(key), dict):
            out[key] = pick(values[key], sub)
        else:
            out[key] = values.get(key)
    return out


def apply_patch(stored: M, patch_model: type[BaseModel], body: Any) -> Patched[M]:
    """Raises pydantic.ValidationError when the body or the result is invalid."""
    patch = patch_model.model_validate(body, context={"partial": True})
    sent = patch.model_dump(exclude_unset=True)
    base = stored.model_dump(exclude_computed_fields=True)  # pydantic 2.12+
    merged = deep_merge(base, sent)
    model = type(stored).model_validate(merged, by_name=True)  # pydantic 2.11+
    return Patched(model=model, changes=pick(model.model_dump(), sent))
