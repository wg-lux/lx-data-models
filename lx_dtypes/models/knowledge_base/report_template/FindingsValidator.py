from typing import Any, Dict, List

from pydantic import Field

from lx_dtypes.factories import str_unknown_factory
from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.report_template.FindingsValidatorDataDict import (
    FindingsValidatorDataDict,
)


class FindingsValidator(KnowledgebaseBaseModel[FindingsValidatorDataDict]):
    query: Dict[str, Any] = Field(default_factory=dict)
    finding: str = Field(default_factory=str_unknown_factory)
    operator: str = "exists"

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return []

    @property
    def ddict_class(self) -> type[FindingsValidatorDataDict]:
        return FindingsValidatorDataDict
