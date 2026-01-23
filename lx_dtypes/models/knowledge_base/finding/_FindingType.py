from typing import List

from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.finding.FindingTypeDataDict import (
    FindingTypeDataDict,
)
from lx_dtypes.names import FINDING_TYPE_MODEL_LIST_TYPE_FIELDS


class FindingType(KnowledgebaseBaseModel[FindingTypeDataDict]):
    @classmethod
    def list_type_fields(cls) -> List[str]:
        """
        Get the field names that are treated as list-type attributes for the FindingType model.

        Returns:
            list_type_fields (List[str]): A list of attribute names that should be handled as lists.
        """
        return FINDING_TYPE_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[FindingTypeDataDict]:
        """
        The data-dict class associated with this model.

        Returns:
            type[FindingTypeDataDict]: The FindingTypeDataDict class used to represent this model's data dictionary.
        """
        return FindingTypeDataDict
