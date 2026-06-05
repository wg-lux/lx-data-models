from __future__ import annotations

from types import NoneType


type JsonNull = NoneType
type JsonScalar = str | int | float | bool
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]
type JsonStringObject = dict[str, str]
type JsonNumericObject = dict[str, JsonScalar]

__all__ = ["JsonNull", "JsonObject", "JsonScalar", "JsonValue"]
