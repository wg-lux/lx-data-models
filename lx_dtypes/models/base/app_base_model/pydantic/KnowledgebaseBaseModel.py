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
        """
        The DataDict class associated with this model.

        Returns:
            ddict_cls (type[DDictT]): The DataDict class used to materialize the model's `ddict` property.
        """

    @classmethod
    @abstractmethod
    def list_type_fields(cls) -> List[str]:
        """
        List field names in the associated DataDict.

        Returns:
            list_of_fields (List[str]): Names of fields in the DataDict that are lists.
        """

    @property
    def ddict(self) -> DDictT:
        """
        Return the DataDict instance represented by this model.

        @returns
            DDictT: The materialized DataDict instance.
        """
        return self.ddict_class(**self.model_dump())

    @model_validator(mode="before")
    @classmethod
    def _coerce_list_fields(cls, data: Any) -> Any:
        """
        Coerces fields declared as list-type from their serialized string form into Python lists.

        Parameters:
            data (Any): Input data mapping (typically the raw values passed to the model validator). Keys listed by `cls.list_type_fields()` will be converted.

        Returns:
            dict: A dictionary with the same keys as `data` where each field named by `cls.list_type_fields()` is replaced by the result of `parse_str_list` (a Python list or None).
        """
        data = dict(data)
        for field in cls.list_type_fields():
            data[field] = parse_str_list(data.get(field))
        return data

    def model_dump(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Dump the model to a dictionary, serializing configured list-type fields to string form.

        Returns:
            dict: Model data with fields returned by `list_type_fields()` converted to their serialized string-list representation.
        """
        dumped = super().model_dump(*args, **kwargs)
        for field in self.list_type_fields():
            dumped[field] = serialize_str_list(dumped[field])
        return dumped

    @classmethod
    def validate_ddict(cls, input_dict: Dict[str, Any]) -> bool:
        """
        Validate that a mapping can be used to construct the model and its associated DataDict.

        Parameters:
            input_dict (Dict[str, Any]): Candidate data to validate against the model and to materialize the model's DataDict.

        Returns:
            True if the dictionary can be validated and the DataDict instantiated.

        Raises:
            ValueError: If model validation or DataDict materialization fails; message includes the original error.
        """
        try:
            instance = cls.model_validate(input_dict)
            _ = instance.ddict  # ensure ddict can be materialized
            return True
        except Exception as e:
            raise ValueError(f"Invalid DataDict: {e}")
