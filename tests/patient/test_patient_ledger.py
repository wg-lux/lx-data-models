from lx_dtypes.models.patient.patient import Patient
from lx_dtypes.models.patient.patient_ledger import PatientLedger
from lx_dtypes.models.patient_interface import PatientInterface


class TestPatientLedgerModel:
    def test_patient_ledger_model(
        self,
        sample_patient_ledger: PatientLedger,
        sample_patient: Patient,
        sample_patient_ledger_patient_uuid: str,
    ):
        ledger = sample_patient_ledger
        uuid = sample_patient_ledger_patient_uuid
        assert uuid in ledger.patients
        assert ledger.patients[uuid] == sample_patient

    def test_patient_ledger_add_pe_to_missing_patient_raises(
        self,
        sample_patient_interface: PatientInterface,
        examination_name_colonoscopy: str,
    ):
        invalid_uuid = "non-existent-uuid"
        try:
            sample_patient_interface.create_patient_examination(
                patient_uuid=invalid_uuid,
                examination_name=examination_name_colonoscopy,
            )
        except ValueError as e:
            assert (
                str(e)
                == f"Patient with UUID {invalid_uuid} does not exist in the ledger."
            )
        else:
            assert False, "Expected KeyError was not raised."

    def test_patient_ledger_examination_exists_not(
        self, sample_patient_ledger: PatientLedger
    ):
        ledger = sample_patient_ledger
        assert not ledger._examination_exists("non-existent-exam-uuid")  # type: ignore
