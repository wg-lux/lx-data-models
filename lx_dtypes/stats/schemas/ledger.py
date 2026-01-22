from typing import Any, ClassVar

import pandera.pandas as pa

from lx_dtypes.models.ledger.center.Pydantic import Center
from lx_dtypes.models.ledger.examiner.Pydantic import Examiner
from lx_dtypes.models.ledger.p_examination.Pydantic import SerializedPExamination
from lx_dtypes.models.ledger.p_finding.Pydantic import SerializedPFinding
from lx_dtypes.models.ledger.p_finding_classification_choice.Pydantic import (
    SerializedPFindingClassificationChoice,
)
from lx_dtypes.models.ledger.p_finding_classification_choice_descriptor.Pydantic import (
    PFindingClassificationChoiceDescriptor,
)
from lx_dtypes.models.ledger.p_finding_classifications.Pydantic import (
    SerializedPFindingClassifications,
)
from lx_dtypes.models.ledger.p_indication.Pydantic import PIndication
from lx_dtypes.models.ledger.p_intervention.Pydantic import PFindingIntervention
from lx_dtypes.models.ledger.p_interventions.Pydantic import (
    SerializedPFindingInterventions,
)
from lx_dtypes.models.ledger.patient.Pydantic import Patient

from .common import COERCE, PANDERA_PYDANTIC_MODEL


class PatientDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(Patient)


class CenterDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(Center)


class ExaminerDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(Examiner)


class PExaminationDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(SerializedPExamination)


class PFindingDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(SerializedPFinding)


class PIndicationDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(PIndication)


class PFindingClassificationsDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(SerializedPFindingClassifications)


class PFindingClassificationChoiceDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(
            SerializedPFindingClassificationChoice
        )


class PFindingClassificationChoiceDescriptorDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(
            PFindingClassificationChoiceDescriptor
        )


class PFindingInterventionsDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(SerializedPFindingInterventions)


class PFindingInterventionDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(PFindingIntervention)
