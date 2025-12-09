from typing import Tuple

from pytest import fixture

from lx_dtypes.models.patient.patient_examination import PatientExamination
from lx_dtypes.models.patient.patient_finding import PatientFinding
from lx_dtypes.models.patient_interface import PatientInterface


@fixture(scope="function")
def sample_patient_examination(
    sample_patient_interface: PatientInterface,
    sample_patient_ledger_patient_uuid: str,
    examination_name_colonoscopy: str,
) -> Tuple[PatientExamination, PatientInterface]:
    patient_examination = sample_patient_interface.create_patient_examination(
        patient_uuid=sample_patient_ledger_patient_uuid,
        examination_name=examination_name_colonoscopy,
    )

    return patient_examination, sample_patient_interface


@fixture(scope="function")
def sample_patient_finding_colon_polyp(
    sample_patient_examination: Tuple[PatientExamination, PatientInterface],
    finding_name_colon_polyp: str,
) -> Tuple[PatientFinding, PatientInterface]:
    patient_examination, sample_patient_interface = sample_patient_examination
    finding = sample_patient_interface.create_examination_finding(
        examination_uuid=patient_examination.uuid,
        finding_name=finding_name_colon_polyp,
    )
    return finding, sample_patient_interface
