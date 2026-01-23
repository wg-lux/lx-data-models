from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.KnowledgebaseBaseModelDjango import (
    KnowledgebaseBaseModelDjango,
)
from lx_dtypes.names import FINDING_MODEL_LIST_TYPE_FIELDS, FieldNames

from .FindingDataDict import (
    FindingDataDict,
)

if TYPE_CHECKING:
    from lx_dtypes.models.knowledge_base.classification._ClassificationDjango import (
        ClassificationDjango,
    )
    from lx_dtypes.models.knowledge_base.intervention.InterventionDjango import (
        InterventionDjango,
    )

    from ._FindingTypeDjango import (
        FindingTypeDjango,
    )


class FindingDjango(KnowledgebaseBaseModelDjango[FindingDataDict]):
    interventions: models.ManyToManyField[
        "InterventionDjango", "InterventionDjango"
    ] = models.ManyToManyField(
        "InterventionDjango",
        related_name=FieldNames.FINDINGS.value,
    )
    finding_types: models.ManyToManyField["FindingTypeDjango", "FindingTypeDjango"] = (
        models.ManyToManyField(
            "FindingTypeDjango", related_name=FieldNames.FINDINGS.value
        )
    )
    classifications: models.ManyToManyField[
        "ClassificationDjango", "ClassificationDjango"
    ] = models.ManyToManyField(
        "ClassificationDjango",
        related_name=FieldNames.FINDINGS.value,
    )

    @property
    def ddict_class(self) -> type[FindingDataDict]:
        """
        Expose the model's associated data-dict class.

        Returns:
            type[FindingDataDict]: The FindingDataDict class associated with this model.
        """
        return FindingDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        """
        Provide the field names used as the finding model's listing/type fields.

        Returns:
            list[str]: The list of field names defined by FINDING_MODEL_LIST_TYPE_FIELDS.
        """
        return FINDING_MODEL_LIST_TYPE_FIELDS
