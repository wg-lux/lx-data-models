from typing import Any, ClassVar

import pandera.pandas as pa

from lx_dtypes.models.examiner.examiner import ExaminerShallow
from lx_dtypes.models.patient.patient import PatientShallow
from lx_dtypes.models.patient.patient_classification_choice_descriptor import (
    PatientFindingClassificationChoiceDescriptorShallow,
)
from lx_dtypes.models.patient.patient_examination import PatientExaminationShallow
from lx_dtypes.models.patient.patient_finding import PatientFindingShallow
from lx_dtypes.models.patient.patient_finding_classification_choice import (
    PatientFindingClassificationChoiceShallow,
)
from lx_dtypes.models.patient.patient_finding_classifications import (
    PatientFindingClassificationsShallow,
)
from lx_dtypes.models.shallow.center import CenterShallow

from .common import COERCE, PANDERA_PYDANTIC_MODEL


# Patient
class PatientShallowSchema(pa.DataFrameModel):
    class Config:  # type:ignore # (pa.DataFrameModel.Config):
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(PatientShallow)
        coerce = COERCE


class PatientExaminationShallowSchema(pa.DataFrameModel):
    class Config:  # type:ignore
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(PatientExaminationShallow)
        coerce = COERCE


class PatientFindingShallowSchema(pa.DataFrameModel):
    class Config:  # type:ignore
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(PatientFindingShallow)
        coerce = COERCE


class PatientFindingClassificationsShallowSchema(pa.DataFrameModel):
    class Config:  # type:ignore
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(
            PatientFindingClassificationsShallow
        )
        coerce = COERCE


class PatientFindingClassificationChoiceShallowSchema(pa.DataFrameModel):
    class Config:  # type:ignore
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(
            PatientFindingClassificationChoiceShallow
        )
        coerce = COERCE


class PatientFindingClassificationChoiceDescriptorShallowSchema(pa.DataFrameModel):
    class Config:  # type:ignore
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(
            PatientFindingClassificationChoiceDescriptorShallow
        )
        coerce = COERCE


class CenterShallowSchema(pa.DataFrameModel):
    class Config:  # type:ignore
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(CenterShallow)
        coerce = COERCE


# Examiner
class ExaminerShallowSchema(pa.DataFrameModel):
    class Config:  # type:ignore
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(ExaminerShallow)
        coerce = COERCE
