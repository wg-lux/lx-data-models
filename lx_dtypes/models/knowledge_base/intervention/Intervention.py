from typing import List, Union

from pydantic import Field

from lx_dtypes.factories.typed_lists import list_of_str_factory
from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.intervention.InterventionDataDict import (
    InterventionDataDict,
)
from lx_dtypes.names import INTERVENTION_MODEL_LIST_TYPE_FIELDS


class Intervention(KnowledgebaseBaseModel[InterventionDataDict]):
    intervention_types: Union[str, List[str]] = Field(
        default_factory=list_of_str_factory
    )

    @classmethod
    def list_type_fields(cls) -> List[str]:
        """
        Provide the list of field names that represent list-typed fields for this model.

        Returns:
            list_type_fields (List[str]): Field names that should be treated as lists.
        """
        return INTERVENTION_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[InterventionDataDict]:
        """
        The data-dictionary class associated with this model.

        Returns:
            The InterventionDataDict class used to represent this model's data dictionary.
        """
        return InterventionDataDict
