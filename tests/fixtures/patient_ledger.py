from pytest import fixture

from lx_dtypes.models.base_models.patient import Patient
from lx_dtypes.models.base_models.patient_ledger import PatientLedger


@fixture(scope="session")
def sample_patient_ledger(sample_patient: Patient) -> PatientLedger:
    ledger = PatientLedger()
    ledger.add_patient(sample_patient)
    return ledger
