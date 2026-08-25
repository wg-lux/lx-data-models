from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from typing import Any, Generic, TypeVar, cast

from pydantic import SerializationInfo, field_serializer, model_validator

from lx_dtypes.serialization import parse_str_list, serialize_str_list

DDictT = TypeVar("DDictT")


class DDictMixIn(Generic[DDictT], ABC):
    @property
    @abstractmethod
    def ddict_class(self) -> type[DDictT]:
        """Return the DataDict class associated with this model."""

    @property
    def ddict(self) -> DDictT:
        """Materialize the associated DataDict from the model's data."""
        data = cast(Any, self).model_dump()
        return self.ddict_class(**data)

    @classmethod
    def validate_ddict(cls, input_dict: Mapping[str, Any]) -> bool:
        """Validate that `input_dict` can construct the model and its DataDict."""
        try:
            instance = cls.model_validate(dict(input_dict))  # type: ignore
            _ = instance.ddict
            return True
        except Exception as exc:  # pragma: no cover - propagates context
            raise ValueError(f"Invalid DataDict: {exc}") from exc


class ListFieldSerializationMixIn(ABC):
    @classmethod
    def list_type_fields(cls) -> list[str]:
        """Default implementation, to be overridden by subclasses."""
        return []

    @classmethod
    def _get_all_list_fields(cls) -> set[str]:
        """Aggregate declared list fields across the MRO, failing on bad declarations."""
        all_fields: set[str] = set()
        for base in cls.__mro__:
            func = getattr(base, "list_type_fields", None)
            if func is None or not callable(func):
                continue
            fields = func()
            if isinstance(fields, (str, bytes)) or not isinstance(fields, Iterable):
                raise TypeError(
                    f"{base.__module__}.{base.__qualname__}.list_type_fields() "
                    "must return an iterable of field names."
                )
            normalized_fields = list(fields)
            if not all(isinstance(field, str) for field in normalized_fields):
                raise TypeError(
                    f"{base.__module__}.{base.__qualname__}.list_type_fields() "
                    "must contain only strings."
                )
            all_fields.update(cast(list[str], normalized_fields))
        return all_fields

    @model_validator(mode="before")
    @classmethod
    def _coerce_list_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        data_copy = data.copy()
        for field in cls._get_all_list_fields():
            if field in data_copy:
                data_copy[field] = parse_str_list(data_copy.get(field))
        return data_copy

    @field_serializer("*", mode="plain", check_fields=False)
    def _serialize_list_fields(self, value: Any, info: SerializationInfo) -> Any:
        fname = getattr(info, "field_name", None)

        if fname and fname in self._get_all_list_fields():
            return serialize_str_list(value)
        return value

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Serialize list fields to their configured string representation."""
        dumped = cast(dict[str, Any], super().model_dump(*args, **kwargs))  # type: ignore
        for field in self._get_all_list_fields():
            value = dumped.get(field)
            if isinstance(value, str):
                continue
            if value is None:
                dumped[field] = ""
                continue
            dumped[field] = serialize_str_list(value)
        return dumped
