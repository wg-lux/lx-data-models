from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lx_dtypes.models.patient.patient_examination import PatientExamination
    from lx_dtypes.models.patient.patient_finding import PatientFinding
    from lx_dtypes.models.patient_interface import PatientInterface


def create_patient_examination(
    patient_interface: "PatientInterface", patient_uuid: str, examination_name: str
) -> "PatientExamination":
    from lx_dtypes.models.patient.patient_examination import PatientExamination

    if not patient_interface.examination_exists(examination_name):
        raise ValueError(
            f"Examination '{examination_name}' does not exist in the knowledge base."
        )

    examination = PatientExamination.create(
        patient_uuid=patient_uuid,
        examination_name=examination_name,
        examination_template=None,
    )

    patient_interface.patient_ledger.add_patient_examination(examination)
    return examination


def create_examination_finding(
    patient_interface: "PatientInterface", examination_uuid: str, finding_name: str
) -> "PatientFinding":
    examination = patient_interface.get_patient_examination_by_uuid(examination_uuid)
    if not patient_interface.finding_exists(finding_name):
        raise ValueError(
            f"Finding '{finding_name}' does not exist in the knowledge base."
        )

    finding = examination.create_finding(finding_name)
    return finding
