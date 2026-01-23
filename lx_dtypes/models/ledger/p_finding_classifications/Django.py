from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.LedgerBaseModelDjango import (
    LedgerBaseModelDjango,
)
from lx_dtypes.names import (
    P_FINDING_CLASSIFICATIONS_MODEL_LIST_TYPE_FIELDS,
    P_FINDING_CLASSIFICATIONS_MODEL_NESTED_FIELDS,
    FieldNames,
)

from .DataDict import (
    PFindingClassificationsDataDict,
)

if TYPE_CHECKING:
    from lx_dtypes.models.ledger.p_finding.Django import (
        PFindingDjango,
    )
    from lx_dtypes.models.ledger.p_finding_classification_choice.Django import (
        PFindingClassificationChoiceDjango,
    )


class PFindingClassificationsDjango(
    LedgerBaseModelDjango[PFindingClassificationsDataDict]
):
    patient_finding: models.ForeignKey["PFindingDjango", "PFindingDjango"] = (
        models.ForeignKey(
            "PFindingDjango",
            related_name=FieldNames.PATIENT_FINDING_CLASSIFICATIONS.value,
            on_delete=models.CASCADE,
        )
    )

    if TYPE_CHECKING:
        patient_finding_classification_choices: models.Manager[
            "PFindingClassificationChoiceDjango"
        ]

    @property
    def ddict_class(self) -> type[PFindingClassificationsDataDict]:
        return PFindingClassificationsDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return P_FINDING_CLASSIFICATIONS_MODEL_LIST_TYPE_FIELDS

    @classmethod
    def nested_fields(cls) -> list[str]:
        return P_FINDING_CLASSIFICATIONS_MODEL_NESTED_FIELDS

    class Meta(LedgerBaseModelDjango.Meta):
        abstract = False
