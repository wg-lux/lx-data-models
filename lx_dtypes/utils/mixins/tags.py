from typing import List

from pydantic import Field, field_validator


def _list_of_strings() -> List[str]:
    return []


class TaggedBaseModelMixin:
    tags: List[str] = Field(default_factory=_list_of_strings)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        # TODO
        # 1. Deduplicate (set)
        # 2. Sort (sorted)
        # 3. Return (must return the value)
        return sorted(list(set(v)))
