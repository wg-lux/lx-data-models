from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, TypeVar, Set, Iterable, cast

from pydantic import model_validator, field_serializer, SerializationInfo
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
        return self.ddict_class(**self.model_dump())  # type: ignore

    @classmethod
    def validate_ddict(cls, input_dict: Dict[str, Any]) -> bool:
        """Validate that `input_dict` can construct the model and its DataDict."""
        try:
            instance = cls.model_validate(input_dict)  # type: ignore
            _ = instance.ddict
            return True
        except Exception as exc:  # pragma: no cover - propagates context
            raise ValueError(f"Invalid DataDict: {exc}") from exc


class ListFieldSerializationMixIn(ABC):
    @classmethod
    def list_type_fields(cls) -> List[str]:
        """Default implementation, to be overridden by subclasses."""
        return []

    @classmethod
    def _get_all_list_fields(cls) -> Set[str]:
        """Safely aggregates fields from the MRO."""
        all_fields: Set[str] = set()
        for base in cls.__mro__:
            func = getattr(base, "list_type_fields", None)
            if func and callable(func):
                try:
                    fields = func()
                    if isinstance(fields, Iterable):
                        all_fields.update(cast(Iterable[str], fields))
                except Exception:
                    continue
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