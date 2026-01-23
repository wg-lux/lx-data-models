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
        """
        Provide the field names that should be treated as list-type fields for InterventionType.

        Returns:
            List[str]: Field names used when representing an InterventionType as a list.
        """
        return INTERVENTION_TYPE_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[InterventionTypeDataDict]:
        """
        The data dictionary class associated with this model.

        Returns:
            type[InterventionTypeDataDict]: The InterventionTypeDataDict class.
        """
        return InterventionTypeDataDict
