from abc import ABC, abstractmethod
from typing import Any, ClassVar, Dict, Generic, List, TypeVar

from pydantic import Field, model_validator

from lx_dtypes.serialization import parse_str_list, serialize_str_list

from .AppBaseModelUUIDTags import (
    AppBaseModelUUIDTags,
)

DDictT = TypeVar("DDictT")


class LedgerBaseModel(AppBaseModelUUIDTags, ABC, Generic[DDictT]):
    external_ids: Dict[str, str] = Field(default_factory=dict)
    serialized_model_cls: ClassVar[Any] = None
    serialized_ddict_cls: ClassVar[Any] = None

    @property
    @abstractmethod
    def ddict_class(self) -> type[DDictT]:
        """Return the DataDict type associated with this model."""

    @property
    def serialized_ddict_class(self) -> type[Any]:
        """Return the DataDict used for serialized export (defaults to ddict_class)."""

        return self.serialized_ddict_cls or self.ddict_class

    @classmethod
    @abstractmethod
    def list_type_fields(cls) -> List[str]:
        """Return a list of fields that are lists in the DataDict."""

    @classmethod
    @abstractmethod
    def nested_fields(cls) -> List[str]:
        """Return a list of fields that are nested DataDicts in the DataDict."""

    @classmethod
    def serialized_model_class(cls) -> "type[LedgerBaseModel[Any]]":
        """Return the model used for serialized export (defaults to self class)."""

        return cls.serialized_model_cls or cls

    @property
    def ddict(self) -> DDictT:
        """Materialize the DataDict using the model contents."""
        return self.ddict_class(**self.model_dump())

    @property
    def serialized_ddict(self) -> Any:
        """Flatten nested ledger models to UUIDs and export serialized DataDict."""

        data = self.model_dump()
        for field in self.nested_fields():
            data[field] = self._flatten_nested(data.get(field))

        serialized_model = self.serialized_model_class().model_validate(data)
        return self.serialized_ddict_class(**serialized_model.model_dump())

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

    def _flatten_nested(self, value: Any) -> Any:
        """Recursively replace nested LedgerBaseModel instances with their UUID strings."""

        if isinstance(value, LedgerBaseModel):
            return str(value.uuid)
        if isinstance(value, list):
            flattened_items = [self._flatten_nested(v) for v in value]
            # If list contains only identifiers/strings (including empty), export as comma-separated string
            if all(isinstance(v, str) for v in flattened_items):
                return serialize_str_list(flattened_items)
            return flattened_items
        if isinstance(value, dict):
            # If the dict already looks like a ledger ddict, collapse to its UUID
            if "uuid" in value:
                return str(value["uuid"])
            return {k: self._flatten_nested(v) for k, v in value.items()}
        return value

    @classmethod
    def validate_ddict(cls, input_dict: Dict[str, Any]) -> bool:
        success = False
        try:
            _ddict_instance = cls.ddict
            success = True
        except Exception as e:
            raise ValueError(f"Invalid DataDict: {e}")
        return success
