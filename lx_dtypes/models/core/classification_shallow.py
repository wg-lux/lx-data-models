from typing import List, TypedDict

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import list_of_str_factory
from lx_dtypes.utils.mixins.base_model import BaseModelMixin
from lx_dtypes.utils.mixins.tags import TaggedMixin


class ClassificationTypeShallowDataDict(TypedDict):
    name: str
    description: str


class ClassificationShallowDataDict(TypedDict):
    name: str
    description: str
    choice_names: List[str]
    type_names: List[str]


class ClassificationTypeShallow(BaseModelMixin, TaggedMixin):
    """Label metadata for a classification type without nested relations."""

    @property
    def ddict_shallow(self) -> type[ClassificationTypeShallowDataDict]:
        return ClassificationTypeShallowDataDict

    def to_ddict_shallow(self) -> ClassificationTypeShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict


class ClassificationShallow(BaseModelMixin, TaggedMixin):
    """Classification stub that links to choice and type names only."""

    choice_names: List[str] = Field(default_factory=list_of_str_factory)
    type_names: List[str] = Field(default_factory=list_of_str_factory)

    @property
    def ddict_shallow(self) -> type[ClassificationShallowDataDict]:
        return ClassificationShallowDataDict

    def to_ddict_shallow(self) -> ClassificationShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict
