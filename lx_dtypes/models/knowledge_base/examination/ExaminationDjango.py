from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.KnowledgebaseBaseModelDjango import (
    KnowledgebaseBaseModelDjango,
)
from lx_dtypes.names import EXAMINATION_MODEL_LIST_TYPE_FIELDS, FieldNames

from .ExaminationDataDict import (
    ExaminationDataDict,
)

if TYPE_CHECKING:
    from lx_dtypes.models.knowledge_base.finding._FindingDjango import (
        FindingDjango,
    )
    from lx_dtypes.models.knowledge_base.indication.IndicationDjango import (
        IndicationDjango,
    )

    from .ExaminationTypeDjango import (
        ExaminationTypeDjango,
    )


class ExaminationDjango(KnowledgebaseBaseModelDjango[ExaminationDataDict]):
    examination_types: models.ManyToManyField[
        "ExaminationTypeDjango", "ExaminationTypeDjango"
    ] = models.ManyToManyField(
        "ExaminationTypeDjango", related_name=FieldNames.EXAMINATIONS.value
    )
    findings: models.ManyToManyField["FindingDjango", "FindingDjango"] = (
        models.ManyToManyField(
            "FindingDjango", related_name=FieldNames.EXAMINATIONS.value
        )
    )
    indications: models.ManyToManyField["IndicationDjango", "IndicationDjango"] = (
        models.ManyToManyField(
            "IndicationDjango", related_name=FieldNames.EXAMINATIONS.value
        )
    )

    @property
    def ddict_class(self) -> type[ExaminationDataDict]:
        """
        Return the data-dictionary class corresponding to this model.

        Returns:
            type[ExaminationDataDict]: The ExaminationDataDict class used to represent this model's structured data.
        """
        return ExaminationDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        """
        List the model field names that should be treated as list types for this model.

        Returns:
            list[str]: Field names that represent list-valued relationships or collections.
        """
        return EXAMINATION_MODEL_LIST_TYPE_FIELDS
