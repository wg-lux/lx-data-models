from typing import List

from pydantic import Field

from lx_dtypes.models.base_models.base_model import (
    KnowledgebaseBaseModel,
    KnowledgebaseBaseModelDataDict,
)
from lx_dtypes.utils.factories.field_defaults import list_of_str_factory


class ClassificationTypeShallowDataDict(KnowledgebaseBaseModelDataDict):
    pass


class ClassificationShallowDataDict(KnowledgebaseBaseModelDataDict):
    pass
    choice_names: List[str]
    type_names: List[str]


class ClassificationTypeShallow(KnowledgebaseBaseModel):
    """Label metadata for a classification type without nested relations."""

    @property
    def ddict_shallow(self) -> type[ClassificationTypeShallowDataDict]:
        return ClassificationTypeShallowDataDict

    def to_ddict_shallow(self) -> ClassificationTypeShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict


class ClassificationShallow(KnowledgebaseBaseModel):
    """Classification stub that links to choice and type names only."""

    choice_names: List[str] = Field(default_factory=list_of_str_factory)
    type_names: List[str] = Field(default_factory=list_of_str_factory)

    @property
    def ddict_shallow(self) -> type[ClassificationShallowDataDict]:
        return ClassificationShallowDataDict

    def to_ddict_shallow(self) -> ClassificationShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict
