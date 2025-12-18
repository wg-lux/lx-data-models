from typing import List

from pydantic import Field

from lx_dtypes.models.base_models.base_model import (
    AppBaseModelNamesUUIDTags,
    AppBaseModelNamesUUIDTagsDataDict,
)
from lx_dtypes.utils.factories.field_defaults import list_of_str_factory, uuid_factory


class CenterShallowDataDict(AppBaseModelNamesUUIDTagsDataDict):
    examiner_uuids: List[str]


class CenterShallow(AppBaseModelNamesUUIDTags):
    """Center shallow model."""

    uuid: str = Field(default_factory=uuid_factory)
    examiner_uuids: List[str] = Field(default_factory=list_of_str_factory)

    @property
    def ddict_shallow(self) -> type[CenterShallowDataDict]:
        return CenterShallowDataDict

    def to_ddict_shallow(self) -> CenterShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict
