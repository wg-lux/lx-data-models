from typing import List, Union

from pydantic import Field

from lx_dtypes.factories.typed_lists import list_of_str_factory
from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.finding.FindingDataDict import FindingDataDict
from lx_dtypes.names import FINDING_MODEL_LIST_TYPE_FIELDS


class Finding(KnowledgebaseBaseModel[FindingDataDict]):
    finding_types: Union[str, List[str]] = Field(default_factory=list_of_str_factory)
    classifications: Union[str, List[str]] = Field(default_factory=list_of_str_factory)
    interventions: Union[str, List[str]] = Field(default_factory=list_of_str_factory)

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return FINDING_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[FindingDataDict]:
        return FindingDataDict
