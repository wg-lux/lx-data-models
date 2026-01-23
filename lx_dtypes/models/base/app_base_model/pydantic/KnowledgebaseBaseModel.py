from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, TypeVar

from pydantic import Field, model_validator

from lx_dtypes.factories import str_unknown_factory
from lx_dtypes.serialization import parse_str_list, serialize_str_list

from .AppBaseModelNamesUUIDTags import (
    AppBaseModelNamesUUIDTags,
)

DDictT = TypeVar("DDictT")


class KnowledgebaseBaseModel(AppBaseModelNamesUUIDTags, ABC, Generic[DDictT]):
    kb_module_name: str = Field(default_factory=str_unknown_factory)

    @property
    @abstractmethod
    def ddict_class(self) -> type[DDictT]:
        """Return the DataDict type associated with this model."""

    @classmethod
    @abstractmethod
    def list_type_fields(cls) -> List[str]:
        """Return a list of fields that are lists in the DataDict."""

    @property
    def ddict(self) -> DDictT:
        """Materialize the DataDict using the model contents."""
        return self.ddict_class(**self.model_dump())

    @model_validator(mode="before")
    def _coerce_list_fields(cls, data: Any) -> Any:
        data = dict(data)
        for field in cls.list_type_fields():
            data[field] = parse_str_list(data.get(field))
        return data

    def model_dump(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Dump while converting list-typed fields back to serialized form."""
        dumped = super().model_dump(*args, **kwargs)
        for field in self.list_type_fields():
            dumped[field] = serialize_str_list(dumped[field])
        return dumped

    @classmethod
    def validate_ddict(cls, input_dict: Dict[str, Any]) -> bool:

        try:
            cls.model_validate(input_dict)
            return True
        except Exception as e:
            raise ValueError(f"DDict validation failed for {cls.__name__}: {e}") from e
