from lx_dtypes.models.ledger.patient import Patient
from lx_dtypes.models.patient_interface import PatientInterface


class TestPatientInterfaceModel:
    def test_patient_interface_model(
        self,
        sample_patient_interface: PatientInterface,
        sample_patient: Patient,
        sample_patient_ledger_patient_uuid: str,
    ):
        ledger = sample_patient_interface.patient_ledger
        uuid = sample_patient_ledger_patient_uuid
        assert uuid in ledger.patients
        assert ledger.patients[uuid] == sample_patient

        invalid_name = "Nonexistent"

        assert not sample_patient_interface.examination_exists(invalid_name)
        assert not sample_patient_interface.finding_exists(invalid_name)
        assert not sample_patient_interface.classification_exists(invalid_name)
        assert not sample_patient_interface.classification_choice_exists(invalid_name)
        assert not sample_patient_interface.indication_exists(invalid_name)
