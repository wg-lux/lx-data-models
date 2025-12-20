from typing import Tuple

from lx_dtypes.models.ledger.patient_finding import PatientFinding
from lx_dtypes.models.patient_interface import PatientInterface


class TestPatientFindingClassificationsModel:
    def test_patient_finding_classifications_get_choice_raises(
        self,
        sample_patient_finding_colon_polyp: Tuple[PatientFinding, PatientInterface],
    ):
        finding, _sample_patient_interface = sample_patient_finding_colon_polyp
        classifications = finding.get_or_create_classifications()
        invalid_uuid = "NonExistentChoice"
        try:
            classifications.get_choice_by_uuid(invalid_uuid)
        except ValueError as e:
            assert str(e) == f"Choice with UUID '{invalid_uuid}' not found."
