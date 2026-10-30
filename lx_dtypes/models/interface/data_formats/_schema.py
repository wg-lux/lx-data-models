"""Restore JSON value types from text using a model's validation JSON schema.

Tabular cells and FHIR XML primitives arrive as text and lose the distinction
between strings, numbers, booleans, singletons and lists. The target model's
JSON schema is the only authority used to restore them; anything the schema
does not decide is left unchanged so model validation reports it.
"""

import json
import re
from collections.abc import Mapping, Sequence
from typing import cast

from pydantic import BaseModel

type JsonValue = (
    None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]
)
type Schema = Mapping[str, object]

_INTEGER = re.compile(r"-?(0|[1-9][0-9]*)")
_NUMBER = re.compile(r"-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?")
_JSON_TYPES = {
    bool: "boolean",
    int: "integer",
    float: "number",
    str: "string",
    type(None): "null",
}


class SchemaCoercer:
    def __init__(self, model: type[BaseModel]) -> None:
        self._root: Schema = model.model_json_schema(mode="validation")
        defs = self._root.get("$defs", {})
        self._defs = cast(
            Mapping[str, Schema], defs if isinstance(defs, Mapping) else {}
        )

    @property
    def root(self) -> Schema:
        return self._root

    def property_schema(self, schema: Schema, key: str) -> Schema:
        for arm in self._object_arms(schema):
            properties = arm.get("properties")
            if isinstance(properties, Mapping) and key in properties:
                return self._resolve(cast(Schema, properties[key]))
            additional = arm.get("additionalProperties")
            if isinstance(additional, Mapping):
                return self._resolve(cast(Schema, additional))
        return {}

    def types(self, schema: Schema) -> set[str]:
        """Return the JSON types a schema accepts; empty means unconstrained."""
        result: set[str] = set()
        for arm in self._arms(schema):
            declared = arm.get("type")
            if isinstance(declared, str):
                result.add(declared)
            elif isinstance(declared, Sequence):
                result.update(item for item in declared if isinstance(item, str))
            choices = arm.get("enum", [arm["const"]] if "const" in arm else [])
            if isinstance(choices, Sequence) and not isinstance(choices, str):
                result.update(
                    _JSON_TYPES.get(type(choice), "string") for choice in choices
                )
            if (
                not declared
                and "enum" not in arm
                and "const" not in arm
                and set(arm)
                <= {
                    "title",
                    "description",
                    "default",
                }
            ):
                return set()
        return result

    def coerce(
        self, value: JsonValue, schema: Schema, *, decode_nested: bool
    ) -> JsonValue:
        """Convert text leaves to the scalar type the schema requires.

        With ``decode_nested`` a text value for an array or object field is
        parsed as JSON (tabular cells); otherwise a non-list value for an
        array-only field is wrapped (FHIR XML repetitions).
        """
        schema = self._resolve(schema)
        accepted = self.types(schema)
        if isinstance(value, list):
            items = self._items_schema(schema, len(value))
            return [
                self.coerce(item, item_schema, decode_nested=decode_nested)
                for item, item_schema in zip(value, items, strict=True)
            ]
        if isinstance(value, dict):
            if accepted and "object" not in accepted and "array" in accepted:
                return self.coerce([value], schema, decode_nested=decode_nested)
            object_schema = self._best_object_arm(schema, value)
            return {
                key: self.coerce(
                    item,
                    self.property_schema(object_schema, key),
                    decode_nested=decode_nested,
                )
                for key, item in value.items()
            }
        if not accepted:
            return value
        if isinstance(value, str):
            return self._coerce_text(
                value, schema, accepted, decode_nested=decode_nested
            )
        if "array" in accepted and not (
            {"null", "boolean", "integer", "number", "string"} & accepted
        ):
            return self.coerce([value], schema, decode_nested=decode_nested)
        if (
            accepted == {"string"}
            and isinstance(value, (int, float))
            and not isinstance(value, bool)
        ):
            # Spreadsheet authors often type identifiers as numbers.
            return str(int(value)) if float(value).is_integer() else repr(value)
        return value

    def _coerce_text(
        self, value: str, schema: Schema, accepted: set[str], *, decode_nested: bool
    ) -> JsonValue:
        if "string" in accepted:
            return value
        if "boolean" in accepted and value in ("true", "false"):
            return value == "true"
        if "integer" in accepted and _INTEGER.fullmatch(value):
            return int(value)
        if "number" in accepted and _NUMBER.fullmatch(value):
            return cast(int | float, json.loads(value))
        if decode_nested and accepted & {"array", "object"}:
            try:
                decoded = cast(JsonValue, json.loads(value))
            except json.JSONDecodeError:
                return value
            return self.coerce(decoded, schema, decode_nested=False)
        if not decode_nested and "array" in accepted:
            return self.coerce([value], schema, decode_nested=False)
        return value

    def _resolve(self, schema: Schema) -> Schema:
        seen: set[str] = set()
        while True:
            reference = schema.get("$ref")
            if not isinstance(reference, str) or not reference.startswith("#/$defs/"):
                return schema
            if reference in seen:
                raise ValueError(f"Cyclic schema reference: {reference}")
            seen.add(reference)
            schema = self._defs[reference.removeprefix("#/$defs/")]

    def _arms(self, schema: Schema) -> list[Schema]:
        schema = self._resolve(schema)
        for key in ("anyOf", "oneOf", "allOf"):
            arms = schema.get(key)
            if isinstance(arms, Sequence) and not isinstance(arms, str):
                return [
                    resolved
                    for arm in arms
                    if isinstance(arm, Mapping)
                    for resolved in self._arms(cast(Schema, arm))
                ]
        return [schema]

    def _object_arms(self, schema: Schema) -> list[Schema]:
        return [
            arm
            for arm in self._arms(schema)
            if arm.get("type") == "object" or "properties" in arm
        ]

    def _best_object_arm(
        self, schema: Schema, value: Mapping[str, JsonValue]
    ) -> Schema:
        arms = self._object_arms(schema)
        for arm in arms:
            properties = arm.get("properties")
            if isinstance(properties, Mapping) and set(value) <= set(
                cast(Schema, properties)
            ):
                return arm
        return arms[0] if arms else {}

    def _items_schema(self, schema: Schema, length: int) -> list[Schema]:
        for arm in self._arms(schema):
            if arm.get("type") != "array":
                continue
            prefix = arm.get("prefixItems")
            if isinstance(prefix, Sequence) and not isinstance(prefix, str):
                fixed = [
                    cast(Schema, item) for item in prefix if isinstance(item, Mapping)
                ]
                return (fixed + [{}] * length)[:length]
            items = arm.get("items")
            return [cast(Schema, items) if isinstance(items, Mapping) else {}] * length
        return [{}] * length
