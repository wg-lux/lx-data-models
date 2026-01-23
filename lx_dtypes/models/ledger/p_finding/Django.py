from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.LedgerBaseModelDjango import (
    LedgerBaseModelDjango,
)
from lx_dtypes.names import (
    P_FINDING_MODEL_LIST_TYPE_FIELDS,
    P_FINDING_MODEL_NESTED_FIELDS,
    FieldNames,
)

from .DataDict import (
    PFindingDataDict,
)

if TYPE_CHECKING:
    from lx_dtypes.models.knowledge_base.finding._FindingDjango import (
        FindingDjango,
    )
    from lx_dtypes.models.ledger.p_examination.Django import (
        PExaminationDjango,
    )
    from lx_dtypes.models.ledger.p_finding_classifications.Django import (
        PFindingClassificationsDjango,
    )
    from lx_dtypes.models.ledger.p_interventions.Django import (
        PFindingInterventionsDjango,
    )


class PFindingDjango(LedgerBaseModelDjango[PFindingDataDict]):
    finding: models.ForeignKey["FindingDjango", "FindingDjango"] = models.ForeignKey(
        "FindingDjango",
        related_name=FieldNames.PATIENT_FINDINGS.value,
        on_delete=models.CASCADE,
    )
    patient_examination: models.ForeignKey[
        "PExaminationDjango", "PExaminationDjango"
    ] = models.ForeignKey(
        "PExaminationDjango",
        related_name=FieldNames.PATIENT_FINDINGS.value,
        on_delete=models.CASCADE,
    )

    if TYPE_CHECKING:
        patient_finding_classifications: models.Manager["PFindingClassificationsDjango"]
        patient_finding_interventions: models.Manager["PFindingInterventionsDjango"]

    @property
    def ddict_class(self) -> type[PFindingDataDict]:
        """
        Return the data-dictionary class associated with this model.

        Returns:
            ddict_class (type[PFindingDataDict]): The PFindingDataDict class for this model.
        """
        return PFindingDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        """
        Provide the model field names that represent list-valued relationships.

        Returns:
            list[str]: Field name strings corresponding to fields that contain list values.
        """
        return P_FINDING_MODEL_LIST_TYPE_FIELDS

    @classmethod
    def nested_fields(cls) -> list[str]:
        """
        List the nested field names for the PFinding model.

        Returns:
            list[str]: Field names that represent nested (expanded) relationships for this model.
        """
        return P_FINDING_MODEL_NESTED_FIELDS

    class Meta(LedgerBaseModelDjango.Meta):
        abstract = False
