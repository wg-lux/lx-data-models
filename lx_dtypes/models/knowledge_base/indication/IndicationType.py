from typing import List

from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.indication.IndicationTypeDataDict import (
    IndicationTypeDataDict,
)
from lx_dtypes.names import INDICATION_TYPE_MODEL_LIST_TYPE_FIELDS


class IndicationType(KnowledgebaseBaseModel[IndicationTypeDataDict]):
    @classmethod
    def list_type_fields(cls) -> List[str]:
        """
        Provide the names of model fields that must be treated as lists.

        Returns:
            list_type_fields (List[str]): Field names that are list-typed for this model.
        """
        return INDICATION_TYPE_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[IndicationTypeDataDict]:
        """
        The data-dictionary class associated with this model.

        Returns:
            type[IndicationTypeDataDict]: The class used to represent this model's underlying data dictionary.
        """
        return IndicationTypeDataDict
