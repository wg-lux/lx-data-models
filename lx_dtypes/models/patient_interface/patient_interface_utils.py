from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lx_dtypes.models.patient_interface import PatientInterface


def patient_interface_examination_exists(
    patient_interface: "PatientInterface", examination_name: str
) -> bool:
    try:
        patient_interface.knowledge_base.get_examination(examination_name)
        return True
    except KeyError:
        return False


def patient_interface_finding_exists(
    patient_interface: "PatientInterface", finding_name: str
) -> bool:
    try:
        patient_interface.knowledge_base.get_finding(finding_name)
        return True
    except KeyError:
        return False


def patient_interface_classification_exists(
    patient_interface: "PatientInterface", classification_name: str
) -> bool:
    try:
        patient_interface.knowledge_base.get_classification(classification_name)
        return True
    except KeyError:
        return False


def patient_interface_classification_choice_exists(
    patient_interface: "PatientInterface", choice_name: str
) -> bool:
    try:
        patient_interface.knowledge_base.get_classification_choice(choice_name)
        return True
    except KeyError:
        return False


def patient_interface_indication_exists(
    patient_interface: "PatientInterface", indication_name: str
) -> bool:
    try:
        patient_interface.knowledge_base.get_indication(indication_name)
        return True
    except KeyError:
        return False
