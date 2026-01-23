from typing import List, Union

from pydantic import Field

from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.information_source.InformationSourceDataDict import (
    InformationSourceDataDict,
)
from lx_dtypes.names import INFORMATION_SOURCE_MODEL_LIST_TYPE_FIELDS


class InformationSource(KnowledgebaseBaseModel[InformationSourceDataDict]):
    information_source_types: Union[str, List[str]] = Field(default_factory=list)

    @property
    def ddict_class(self) -> type[InformationSourceDataDict]:
        """
        Return the data-dictionary class associated with this model.

        Returns:
            type[InformationSourceDataDict]: The InformationSourceDataDict class used by this model.
        """
        return InformationSourceDataDict

    @classmethod
    def list_type_fields(cls) -> List[str]:
        """
        Provide the names of model fields that are treated as list types for this class.

        Returns:
            List[str]: Field names in the InformationSource model that should be interpreted as lists.
        """
        return INFORMATION_SOURCE_MODEL_LIST_TYPE_FIELDS
