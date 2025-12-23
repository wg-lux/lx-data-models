from typing import TypedDict, Union

from lx_dtypes.models.ledger.center import CenterDataDict
from lx_dtypes.models.ledger.examiner import ExaminerDataDict
from lx_dtypes.models.ledger.patient import PatientDataDict
from lx_dtypes.models.ledger.patient_classification_choice_descriptor import (
    PatientFindingClassificationChoiceDescriptorDataDict,
)
from lx_dtypes.models.ledger.patient_examination import PatientExaminationDataDict
from lx_dtypes.models.ledger.patient_finding import PatientFindingDataDict
from lx_dtypes.models.ledger.patient_finding_classification_choice import (
    PatientFindingClassificationChoiceDataDict,
)
from lx_dtypes.models.ledger.patient_finding_classifications import (
    PatientFindingClassificationsDataDict,
)
from lx_dtypes.models.ledger.patient_indication import PatientIndicationDataDict

LEDGER_DDICT_LIST = [
    CenterDataDict,
    ExaminerDataDict,
    PatientDataDict,
    PatientExaminationDataDict,
    PatientFindingDataDict,
    PatientFindingClassificationsDataDict,
    PatientFindingClassificationChoiceDataDict,
    PatientFindingClassificationChoiceDescriptorDataDict,
    PatientIndicationDataDict,
]

LEDGER_UNION_DDICT_LIST = Union[
    CenterDataDict,
    ExaminerDataDict,
    PatientDataDict,
    PatientExaminationDataDict,
    PatientFindingDataDict,
    PatientFindingClassificationsDataDict,
    PatientFindingClassificationChoiceDataDict,
    PatientFindingClassificationChoiceDescriptorDataDict,
    PatientIndicationDataDict,
]

LEDGER_UNION_DDICT_TYPE_LIST = Union[
    type[CenterDataDict],
    type[ExaminerDataDict],
    type[PatientDataDict],
    type[PatientExaminationDataDict],
    type[PatientFindingDataDict],
    type[PatientFindingClassificationsDataDict],
    type[PatientFindingClassificationChoiceDataDict],
    type[PatientFindingClassificationChoiceDescriptorDataDict],
    type[PatientIndicationDataDict],
]


class LEDGER_DDICT_BY_NAME_TYPE(TypedDict):
    center: type[CenterDataDict]
    examiner: type[ExaminerDataDict]
    patient: type[PatientDataDict]
    patient_examination: type[PatientExaminationDataDict]
    patient_finding: type[PatientFindingDataDict]
    patient_finding_classifications: type[PatientFindingClassificationsDataDict]
    patient_finding_classification_choice: type[
        PatientFindingClassificationChoiceDataDict
    ]
    patient_finding_classification_choice_descriptor: type[
        PatientFindingClassificationChoiceDescriptorDataDict
    ]
    patient_indication: type[PatientIndicationDataDict]


LEDGER_DDICT_BY_NAME = LEDGER_DDICT_BY_NAME_TYPE(
    center=CenterDataDict,
    examiner=ExaminerDataDict,
    patient=PatientDataDict,
    patient_examination=PatientExaminationDataDict,
    patient_finding=PatientFindingDataDict,
    patient_finding_classifications=PatientFindingClassificationsDataDict,
    patient_finding_classification_choice=PatientFindingClassificationChoiceDataDict,
    patient_finding_classification_choice_descriptor=PatientFindingClassificationChoiceDescriptorDataDict,
    patient_indication=PatientIndicationDataDict,
)

LEDGER_DDICT_BY_NAME_REVERSED = {v: k for k, v in LEDGER_DDICT_BY_NAME.items()}
