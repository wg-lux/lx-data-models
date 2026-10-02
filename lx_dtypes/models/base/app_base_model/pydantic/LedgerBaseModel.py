from abc import abstractmethod
from typing import Any, ClassVar, TypeVar

from pydantic import Field

from lx_dtypes.serialization import serialize_str_list

from .AppBaseModelUUIDTags import (
    AppBaseModelUUIDTags,
)
from .InterfaceMixIns import (
    DDictMixIn,
    ListFieldSerializationMixIn,
)

DDictT = TypeVar("DDictT")


class LedgerBaseModel(
    ListFieldSerializationMixIn,
    AppBaseModelUUIDTags,
    DDictMixIn[DDictT],
    # Generic[DDictT],
):
    external_ids: dict[str, str] = Field(default_factory=dict)
    serialized_model_cls: ClassVar[Any] = None
    serialized_ddict_cls: ClassVar[Any] = None

    @property
    def serialized_ddict_class(self) -> type[Any]:
        """
        The DataDict class used for serialized export.

        If the class sets `serialized_ddict_cls`, that class is returned; otherwise `ddict_class` is returned.

        Returns:
            type[Any]: The DataDict class to use for serialized exports.
        """

        return self.serialized_ddict_cls or self.ddict_class

    @classmethod
    @abstractmethod
    def nested_fields(cls) -> list[str]:
        """
        Return the names of DataDict fields whose values are nested DataDicts.

        Returns:
            list[str]: Field names in the associated DataDict that contain nested DataDict values.
        """

    @classmethod
    def serialized_model_class(cls) -> "type[LedgerBaseModel[Any]]":
        """
        Get the model class used for serialized export.

        Returns:
            model_cls (type[LedgerBaseModel[Any]]): The class to use when producing serialized representations; `serialized_model_cls` if set on the class, otherwise the class itself.
        """

        return cls.serialized_model_cls or cls

    @property
    def serialized_model(self) -> "LedgerBaseModel[Any]":
        """
        Produce a serialized model with nested ledger models replaced by UUID strings.

        Returns:
            An instance of the serialized model class (`serialized_model_class`) containing the model's data with nested ledger items flattened to UUID strings.
        """

        data = self.model_dump()
        for field in self.nested_fields():
            data[field] = self._flatten_nested(data.get(field))

        serialized_model = self.serialized_model_class().model_validate(data)
        return serialized_model

    @property
    def serialized_ddict(self) -> Any:
        """
        Produce a serialized DataDict with nested ledger models replaced by UUID strings.

        Returns:
            An instance of the serialized DataDict class (`serialized_ddict_class`) containing the model's data with nested ledger items flattened to UUID strings.
        """
        serialized_model = self.serialized_model
        return self.serialized_ddict_class(**serialized_model.model_dump())

    def _flatten_nested(self, value: Any) -> Any:
        """
        Recursively flatten nested LedgerBaseModel instances, lists, and dicts into UUID strings or serialized collections.

        Parameters:
            value (Any): Any value that may contain nested LedgerBaseModel instances, lists, or dicts.

        Returns:
            Any: The flattened value:
              - If `value` is a LedgerBaseModel, its `uuid` as a string.
              - If `value` is a list, a list of flattened items, or if every flattened item is a string, a comma-separated string produced by `serialize_str_list`.
              - If `value` is a dict and contains a `"uuid"` key, that UUID as a string; otherwise a dict with each value flattened.
              - Otherwise `value` unchanged.
        """

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
