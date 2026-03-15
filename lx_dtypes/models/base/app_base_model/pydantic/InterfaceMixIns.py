from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Mapping, TypeVar, cast

from pydantic import model_validator

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
    @abstractmethod
    def list_type_fields(cls) -> List[str]:
        """Return names of fields that should be treated as serialized lists."""

    @model_validator(mode="before")
    @classmethod
    def _coerce_list_fields(cls, data: Any) -> Any:
        """Coerce configured fields from serialized strings into Python lists."""
        data = dict(data)
        for field in cls.list_type_fields():
            data[field] = parse_str_list(data.get(field))
        return data

    def model_dump(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Serialize list fields to their configured string representation."""
        dumped = cast(Dict[str, Any], super().model_dump(*args, **kwargs))  # type: ignore
        for field in self.list_type_fields():
            dumped[field] = serialize_str_list(dumped[field])
        return dumped
