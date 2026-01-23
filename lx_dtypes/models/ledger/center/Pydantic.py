from typing import List, Union

from pydantic import Field

from lx_dtypes.factories.literals import str_unknown_factory
from lx_dtypes.factories.typed_lists import list_of_str_factory
from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.names import CENTER_MODEL_LIST_TYPE_FIELDS, CENTER_MODEL_NESTED_FIELDS

from .DataDict import (
    CenterDataDict,
)


class Center(LedgerBaseModel[CenterDataDict]):
    name: str = Field(default_factory=str_unknown_factory)
    examiners: Union[str, List[str]] = Field(default_factory=list_of_str_factory)

    @classmethod
    def list_type_fields(cls) -> List[str]:
        """
        Identify model fields that should be treated as list types.

        Returns:
            List[str]: Field names corresponding to attributes that are list-typed for this model.
        """
        return CENTER_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[CenterDataDict]:
        """
        Associated data dictionary class for the model.

        Returns:
            type[CenterDataDict]: The CenterDataDict class used to represent this model's data dictionary.
        """
        return CenterDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        """
        Provide the model's nested field names.

        Returns:
            List[str]: Field names that represent nested sub-models.
        """
        return CENTER_MODEL_NESTED_FIELDS
