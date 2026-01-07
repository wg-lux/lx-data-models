from typing import List

from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.intervention.InterventionTypeDataDict import (
    InterventionTypeDataDict,
)
from lx_dtypes.names import INTERVENTION_TYPE_MODEL_LIST_TYPE_FIELDS


class InterventionType(KnowledgebaseBaseModel[InterventionTypeDataDict]):
    @classmethod
    def list_type_fields(cls) -> List[str]:
        return INTERVENTION_TYPE_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[InterventionTypeDataDict]:
        return InterventionTypeDataDict
