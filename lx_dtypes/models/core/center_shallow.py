from typing import List, NotRequired, TypedDict

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import list_of_str_factory, uuid_factory
from lx_dtypes.utils.mixins.base_model import BaseModelMixin
from lx_dtypes.utils.mixins.tags import TaggedMixin


class CenterShallowDataDict(TypedDict):
    uuid: str
    name: str
    name_de: NotRequired[str]
    name_en: NotRequired[str]
    description: NotRequired[str]
    tags: NotRequired[List[str]]
    examiner_uuids: List[str]


class CenterShallow(BaseModelMixin, TaggedMixin):
    """Center shallow model."""

    uuid: str = Field(default_factory=uuid_factory)
    examiner_uuids: List[str] = Field(default_factory=list_of_str_factory)

    @property
    def ddict_shallow(self) -> type[CenterShallowDataDict]:
        return CenterShallowDataDict

    def to_ddict_shallow(self) -> CenterShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict
