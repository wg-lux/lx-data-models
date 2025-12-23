from typing import TypedDict, Union

from lx_dtypes.lx_django.models import (
    Center,
    Examiner,
    Patient,
    # PatientExamination,
    # PatientFinding,
    # PatientFindingClassificationChoice,
    # PatientFindingClassificationChoiceDescriptor,
    # PatientFindingClassifications,
    # PatientIndication,
)

LEDGER_DJANGO_MODEL_LIST = [
    Center,
    Examiner,
    Patient,
    # PatientExamination,
    # PatientFinding,
    # PatientFindingClassificationChoice,
    # PatientFindingClassificationChoiceDescriptor,
    # PatientFindingClassifications,
    # PatientIndication,
]

LEDGER_UNION_DJANGO_MODEL_LIST = Union[
    Center,
    Examiner,
    Patient,
    # PatientExamination,
    # PatientFinding,
    # PatientFindingClassificationChoice,
    # PatientFindingClassificationChoiceDescriptor,
    # PatientFindingClassifications,
    # PatientIndication,
]

LEDGER_UNION_DJANGO_MODEL_TYPE_LIST = Union[
    type[Center],
    type[Examiner],
    type[Patient],
    # type[PatientExamination],
    # type[PatientFinding],
    # type[PatientFindingClassificationChoice],
    # type[PatientFindingClassificationChoiceDescriptor],
    # type[PatientFindingClassifications],
    # type[PatientIndication],
]


class LEDGER_DJANGO_MODEL_BY_NAME_TYPE(TypedDict):
    center: type[Center]
    examiner: type[Examiner]
    patient: type[Patient]
    # patient_examination: type[PatientExamination]
    # patient_finding: type[PatientFinding]
    # patient_finding_classifications: type[PatientFindingClassifications]
    # patient_finding_classification_choice: type[PatientFindingClassificationChoice]
    # patient_finding_classification_choice_descriptor: type[PatientFindingClassificationChoiceDescriptor]
    # patient_indication: type[PatientIndication]


LEDGER_DJANGO_MODEL_BY_NAME = LEDGER_DJANGO_MODEL_BY_NAME_TYPE(
    center=Center,
    examiner=Examiner,
    patient=Patient,
    # patient_examination = PatientExamination,
    # patient_finding = PatientFinding,
    # patient_finding_classifications = PatientFindingClassifications,
    # patient_finding_classification_choice = PatientFindingClassificationChoice,
    # patient_finding_classification_choice_descriptor = PatientFindingClassificationChoiceDescriptor,
    # patient_indication = PatientIndication,
)
