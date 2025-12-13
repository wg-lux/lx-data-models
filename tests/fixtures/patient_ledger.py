from pytest import fixture

from lx_dtypes.models.patient.patient import Patient
from lx_dtypes.utils.initialized_models import PatientLedger


@fixture(scope="function")
def sample_patient_ledger(sample_patient: Patient) -> PatientLedger:
    ledger = PatientLedger()
    ledger.add_patient(sample_patient)
    return ledger


@fixture(scope="function")
def sample_patient_ledger_patient_uuid(sample_patient: Patient) -> str:
    return sample_patient.uuid
