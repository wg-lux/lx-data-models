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
        return CENTER_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[CenterDataDict]:
        return CenterDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        return CENTER_MODEL_NESTED_FIELDS
