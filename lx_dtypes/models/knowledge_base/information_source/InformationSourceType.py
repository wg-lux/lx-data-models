from typing import List

from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.information_source.InformationSourceTypeDataDict import (
    InformationSourceTypeDataDict,
)
from lx_dtypes.names import INFORMATION_SOURCE_TYPE_MODEL_LIST_TYPE_FIELDS


class InformationSourceType(KnowledgebaseBaseModel[InformationSourceTypeDataDict]):
    @classmethod
    def list_type_fields(cls) -> List[str]:
        """
        Identify which model fields should be treated as list-type fields.

        Returns:
            list_type_fields (List[str]): List of field names that are considered list-typed for this model.
        """
        return INFORMATION_SOURCE_TYPE_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[InformationSourceTypeDataDict]:
        """
        The data-dict class associated with this model.

        Returns:
            type[InformationSourceTypeDataDict]: The InformationSourceTypeDataDict class used for this model's data representation.
        """
        return InformationSourceTypeDataDict
