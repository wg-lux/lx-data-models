from __future__ import annotations
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
    from lx_dtypes.models.knowledge_base.classification import ClassificationDjango
    from lx_dtypes.models.knowledge_base.finding._FindingTypeDjango import (
        FindingTypeDjango,
    )
    from lx_dtypes.models.knowledge_base.intervention.InterventionDjango import (
        InterventionDjango,
    )


class FindingDjango(KnowledgebaseBaseModelDjango[FindingDataDict]):
    if TYPE_CHECKING:
        interventions: models.ManyToManyField[InterventionDjango, InterventionDjango]
        caused_by_interventions: models.ManyToManyField[
            InterventionDjango, InterventionDjango
        ]
        finding_types: models.ManyToManyField[FindingTypeDjango, FindingTypeDjango]
        classifications: models.ManyToManyField[
            ClassificationDjango, ClassificationDjango
        ]

    interventions = models.ManyToManyField(
        "InterventionDjango",
        related_name=FieldNames.FINDINGS.value,
    )
    caused_by_interventions = models.ManyToManyField(
        "InterventionDjango",
        related_name="caused_by_findings",
        blank=True,
    )
    finding_types = models.ManyToManyField(
        "FindingTypeDjango", related_name=FieldNames.FINDINGS.value
    )
    classifications = models.ManyToManyField(
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
