from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.KnowledgebaseBaseModelDjango import (
    KnowledgebaseBaseModelDjango,
)
from lx_dtypes.names import FINDING_TYPE_MODEL_LIST_TYPE_FIELDS

from .FindingTypeDataDict import (
    FindingTypeDataDict,
)


class FindingTypeDjango(KnowledgebaseBaseModelDjango[FindingTypeDataDict]):
    if TYPE_CHECKING:
        from lx_dtypes.models.knowledge_base.finding._FindingDjango import (
            FindingDjango,
        )

        findings: models.QuerySet["FindingDjango"]

    @property
    def ddict_class(self) -> type[FindingTypeDataDict]:
        """
        Return the data-dict class associated with this model.

        Returns:
            type[FindingTypeDataDict]: The class used to create the model's data-dictionary instances.
        """
        return FindingTypeDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        """
        Provide the list of model field names used when listing finding type information.

        Returns:
            list[str]: Field names from FINDING_TYPE_MODEL_LIST_TYPE_FIELDS.
        """
        return FINDING_TYPE_MODEL_LIST_TYPE_FIELDS
