from typing import List

from pydantic import Field

from lx_dtypes.models.base_models.base_model import (
    AppBaseModelNamesUUIDTags,
    AppBaseModelNamesUUIDTagsDataDict,
    LedgerBaseModel,
    LedgerBaseModelDataDict,
)
from lx_dtypes.utils.factories.field_defaults import list_of_str_factory


class CenterShallowDataDict(AppBaseModelNamesUUIDTagsDataDict, LedgerBaseModelDataDict):  # type: ignore[misc]
    examiner_uuids: List[str]


class CenterShallow(AppBaseModelNamesUUIDTags, LedgerBaseModel):
    """Center shallow model."""

    examiner_uuids: List[str] = Field(default_factory=list_of_str_factory)

    @property
    def ddict_shallow(self) -> type[CenterShallowDataDict]:
        return CenterShallowDataDict

    def to_ddict_shallow(self) -> CenterShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict
