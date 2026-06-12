from __future__ import annotations

from typing import TypedDict


class MultilingualResponseData(TypedDict, total=False):
    id: int
    name: str
    name_de: str
    name_en: str
    description: str
    description_de: str
    description_en: str
    required: bool
    classification_id: int
    choices: list["MultilingualResponseData"]


__all__ = ["MultilingualResponseData"]
