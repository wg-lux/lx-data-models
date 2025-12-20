from typing import Dict, Union

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

LEDGER_DDICT_BY_NAME: Dict[str, LEDGER_UNION_DDICT_TYPE_LIST] = {
    "center": CenterDataDict,
    "examiner": ExaminerDataDict,
    "patient": PatientDataDict,
    "patient_examination": PatientExaminationDataDict,
    "patient_finding": PatientFindingDataDict,
    "patient_finding_classifications": PatientFindingClassificationsDataDict,
    "patient_finding_classification_choice": PatientFindingClassificationChoiceDataDict,
    "patient_finding_classification_choice_descriptor": PatientFindingClassificationChoiceDescriptorDataDict,
    "patient_indication": PatientIndicationDataDict,
}
