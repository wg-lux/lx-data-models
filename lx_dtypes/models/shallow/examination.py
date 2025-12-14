from typing import List, TypedDict

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import list_of_str_factory
from lx_dtypes.utils.mixins.base_model import BaseModelMixin
from lx_dtypes.utils.mixins.tags import TaggedMixin


class ExaminationTypeShallowDataDict(TypedDict):
    name: str
    description: str


class ExaminationShallowDataDict(TypedDict):
    name: str
    description: str
    finding_names: List[str]
    type_names: List[str]
    indication_names: List[str]


class ExaminationTypeShallow(BaseModelMixin, TaggedMixin):
    """Taggable shell for examination types."""

    @property
    def ddict_shallow(self) -> type[ExaminationTypeShallowDataDict]:
        return ExaminationTypeShallowDataDict

    def to_ddict_shallow(self) -> ExaminationTypeShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict


class ExaminationShallow(BaseModelMixin, TaggedMixin):
    """
    Links examinations to finding, type, and indication names without nesting.

    Attributes:
        name (str): The name of the classification choice.
        name_de (str | None): The German name of the classification choice.
        name_en (str | None): The English name of the classification choice.
        description (str | None): The description of the classification choice.
        finding_names (list[str]): Names of associated findings.
        type_names (list[str]): Names of associated examination types.
        indication_names (list[str]): Names of associated indications.

    """

    finding_names: List[str] = Field(default_factory=list_of_str_factory)
    type_names: List[str] = Field(default_factory=list_of_str_factory)
    indication_names: List[str] = Field(default_factory=list_of_str_factory)

    @property
    def ddict_shallow(self) -> type[ExaminationShallowDataDict]:
        return ExaminationShallowDataDict

    def to_ddict_shallow(self) -> ExaminationShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict
