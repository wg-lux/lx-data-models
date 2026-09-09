from __future__ import annotations

import inspect
from collections.abc import Mapping

from pydantic import BaseModel


def direct_parent_field_collisions(
    model_class: type[BaseModel],
) -> dict[str, tuple[type[BaseModel], ...]]:
    """Return fields declared by more than one direct Pydantic parent."""
    direct_parents = tuple(
        parent
        for parent in model_class.__bases__
        if isinstance(parent, type) and issubclass(parent, BaseModel)
    )
    owners: dict[str, list[type[BaseModel]]] = {}
    for parent in direct_parents:
        raw_annotations = inspect.get_annotations(parent, eval_str=False)
        if not isinstance(raw_annotations, Mapping):
            continue
        for field_name in raw_annotations:
            if isinstance(field_name, str) and field_name in parent.model_fields:
                owners.setdefault(field_name, []).append(parent)

    return {
        field_name: tuple(field_owners)
        for field_name, field_owners in owners.items()
        if len(field_owners) > 1
    }


__all__ = ["direct_parent_field_collisions"]
