from lx_dtypes.models.base_models.patient import Patient
from lx_dtypes.models.base_models.patient_ledger import PatientLedger


class TestPatientLedgerModel:
    def test_patient_ledger_model(self, sample_patient_ledger: PatientLedger, sample_patient: Patient):
        ledger = sample_patient_ledger
        assert sample_patient.uuid in ledger.patients
        assert ledger.patients[sample_patient.uuid] == sample_patient
