from typing import TypedDict, Union

from lx_dtypes.models.ledger.center import Center
from lx_dtypes.models.ledger.examiner import Examiner
from lx_dtypes.models.ledger.patient import Patient
from lx_dtypes.models.ledger.patient_classification_choice_descriptor import (
    PatientFindingClassificationChoiceDescriptor,
)
from lx_dtypes.models.ledger.patient_examination import PatientExamination
from lx_dtypes.models.ledger.patient_finding import PatientFinding
from lx_dtypes.models.ledger.patient_finding_classification_choice import (
    PatientFindingClassificationChoice,
)
from lx_dtypes.models.ledger.patient_finding_classifications import (
    PatientFindingClassifications,
)
from lx_dtypes.models.ledger.patient_indication import PatientIndication

LEDGER_PYDANTIC_LIST = [
    Center,
    Examiner,
    Patient,
    PatientExamination,
    PatientFinding,
    PatientFindingClassifications,
    PatientFindingClassificationChoice,
    PatientFindingClassificationChoiceDescriptor,
    PatientIndication,
]

LEDGER_UNION_PYDANTIC_LIST = Union[
    Center,
    Examiner,
    Patient,
    PatientExamination,
    PatientFinding,
    PatientFindingClassifications,
    PatientFindingClassificationChoice,
    PatientFindingClassificationChoiceDescriptor,
    PatientIndication,
]

LEDGER_UNION_PYDANTIC_TYPE_LIST = Union[
    type[Center],
    type[Examiner],
    type[Patient],
    type[PatientExamination],
    type[PatientFinding],
    type[PatientFindingClassifications],
    type[PatientFindingClassificationChoice],
    type[PatientFindingClassificationChoiceDescriptor],
    type[PatientIndication],
]


class LEDGER_PYDANTIC_BY_NAME_TYPE(TypedDict):
    center: type[Center]
    examiner: type[Examiner]
    patient: type[Patient]
    patient_examination: type[PatientExamination]
    patient_finding: type[PatientFinding]
    patient_finding_classifications: type[PatientFindingClassifications]
    patient_finding_classification_choice: type[PatientFindingClassificationChoice]
    patient_finding_classification_choice_descriptor: type[
        PatientFindingClassificationChoiceDescriptor
    ]
    patient_indication: type[PatientIndication]


LEDGER_PYDANTIC_BY_NAME = LEDGER_PYDANTIC_BY_NAME_TYPE(
    center=Center,
    examiner=Examiner,
    patient=Patient,
    patient_examination=PatientExamination,
    patient_finding=PatientFinding,
    patient_finding_classifications=PatientFindingClassifications,
    patient_finding_classification_choice=PatientFindingClassificationChoice,
    patient_finding_classification_choice_descriptor=PatientFindingClassificationChoiceDescriptor,
    patient_indication=PatientIndication,
)
