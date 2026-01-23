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
        """
        The DataDict class associated with this model.

        Returns:
            type[DDictT]: The DataDict type used to construct materialized ddict instances.
        """

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
    def list_type_fields(cls) -> List[str]:
        """
        Identify the DataDict field names whose values are lists.

        Returns:
            List[str]: Field names in the associated DataDict that should be treated as lists.
        """

    @classmethod
    @abstractmethod
    def nested_fields(cls) -> List[str]:
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
    def ddict(self) -> DDictT:
        """
        Materializes the DataDict associated with this model from the model's data.

        Returns:
            ddict (DDictT): An instance of the model's DataDict class constructed from the model's dumped data.
        """
        return self.ddict_class(**self.model_dump())

    @property
    def serialized_ddict(self) -> Any:
        """
        Produce a serialized DataDict with nested ledger models replaced by UUID strings.

        Returns:
            An instance of the serialized DataDict class (`serialized_ddict_class`) containing the model's data with nested ledger items flattened to UUID strings.
        """

        data = self.model_dump()
        for field in self.nested_fields():
            data[field] = self._flatten_nested(data.get(field))

        serialized_model = self.serialized_model_class().model_validate(data)
        return self.serialized_ddict_class(**serialized_model.model_dump())

    @model_validator(mode="before")
    @classmethod
    def _coerce_list_fields(cls, data: Any) -> Any:
        """
        Coerce fields declared as list-type into Python lists within a shallow copy of the input mapping.

        Parameters:
            data (Any): A mapping-like input (will be converted to a dict) whose keys may include fields returned by list_type_fields().

        Returns:
            dict: A shallow copy of the input with each field named in list_type_fields() replaced by the result of parse_str_list(data.get(field)).
        """
        data = dict(data)
        for field in cls.list_type_fields():
            data[field] = parse_str_list(data.get(field))
        return data

    def model_dump(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Return the model's data with any list-typed fields converted to their serialized string form.

        The returned dictionary is the same as the standard model dump except each field named in list_type_fields() is replaced by the value produced by serialize_str_list for that field.

        Returns:
            dict: Model data with list-type fields serialized to comma-separated string representations.
        """
        dumped = super().model_dump(*args, **kwargs)
        for field in self.list_type_fields():
            dumped[field] = serialize_str_list(dumped[field])
        return dumped

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

    @classmethod
    def validate_ddict(cls, input_dict: Dict[str, Any]) -> bool:
        """
        Validate that an input mapping can be converted into this model and materialized as its DataDict.

        Parameters:
            input_dict (Dict[str, Any]): Mapping representing the DataDict to validate.

        Returns:
            bool: `True` if validation and materialization succeed.

        Raises:
            ValueError: If validation or materialization fails; the exception message describes the problem.
        """
        try:
            instance = cls.model_validate(input_dict)
            _ = instance.ddict  # Verify ddict can be materialized
            return True
        except Exception as e:
            raise ValueError(f"Invalid DataDict: {e}")
