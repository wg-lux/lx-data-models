from lx_dtypes.models.knowledge_base import KnowledgeBase
from lx_dtypes.models.patient.patient import Patient
from lx_dtypes.models.patient.patient_examination import PatientExamination
from lx_dtypes.models.patient.patient_finding import PatientFinding
from lx_dtypes.models.patient.patient_finding_classification_choice import (
    PatientFindingClassificationChoice,
)
from lx_dtypes.models.patient.patient_ledger import PatientLedger
from lx_dtypes.utils.mixins.base_model import AppBaseModel

from .patient_interface_create import (
    create_examination_finding,
    create_patient_examination,
)
from .patient_interface_update import (
    add_classification_choice_to_finding,
    add_indication_to_examination,
)
from .patient_interface_utils import (
    patient_interface_classification_choice_exists,
    patient_interface_classification_exists,
    patient_interface_examination_exists,
    patient_interface_finding_exists,
    patient_interface_indication_exists,
)


class PatientInterface(AppBaseModel):
    knowledge_base: KnowledgeBase
    patient_ledger: PatientLedger

    # Create Methods
    def create_patient_examination(
        self, patient_uuid: str, examination_name: str
    ) -> PatientExamination:
        return create_patient_examination(
            patient_interface=self,
            patient_uuid=patient_uuid,
            examination_name=examination_name,
        )

    def create_examination_finding(
        self, examination_uuid: str, finding_name: str
    ) -> PatientFinding:
        return create_examination_finding(
            patient_interface=self,
            examination_uuid=examination_uuid,
            finding_name=finding_name,
        )

    # Utility Methods
    def examination_exists(self, examination_name: str) -> bool:
        return patient_interface_examination_exists(self, examination_name)

    def finding_exists(self, finding_name: str) -> bool:
        return patient_interface_finding_exists(self, finding_name)

    def classification_exists(self, classification_name: str) -> bool:
        return patient_interface_classification_exists(self, classification_name)

    def classification_choice_exists(self, choice_name: str) -> bool:
        return patient_interface_classification_choice_exists(self, choice_name)

    def indication_exists(self, indication_name: str) -> bool:
        return patient_interface_indication_exists(self, indication_name)

    # Get Methods
    def get_patient_by_uuid(self, patient_uuid: str) -> Patient:
        patient = self.patient_ledger.get_patient_by_uuid(patient_uuid)
        return patient

    def get_patient_examination_by_uuid(
        self, examination_uuid: str
    ) -> PatientExamination:
        examination = self.patient_ledger.get_examination_by_uuid(examination_uuid)
        return examination

    def get_patient_finding_by_patient_examination_and_finding_uuid(
        self, examination_uuid: str, finding_uuid: str
    ) -> PatientFinding:
        examination = self.get_patient_examination_by_uuid(examination_uuid)
        finding = examination.get_finding_by_uuid(finding_uuid)
        return finding

    # Update Methods
    def add_classification_choice_to_finding(
        self,
        examination_uuid: str,
        finding_uuid: str,
        classification_name: str,
        choice_name: str,
    ) -> PatientFindingClassificationChoice:
        return add_classification_choice_to_finding(
            patient_interface=self,
            examination_uuid=examination_uuid,
            finding_uuid=finding_uuid,
            classification_name=classification_name,
            choice_name=choice_name,
        )

    def add_indication_to_examination(
        self,
        examination_uuid: str,
        indication_name: str,
    ) -> PatientExamination:
        return add_indication_to_examination(
            patient_interface=self,
            examination_uuid=examination_uuid,
            indication_name=indication_name,
        )

    # Delete Methods
    def delete_examination(self, examination_uuid: str) -> None:
        self.patient_ledger.delete_patient_examination(examination_uuid)

    def delete_patient(self, patient_uuid: str) -> None:
        self.patient_ledger.delete_patient(patient_uuid)

    def delete_finding_from_examination(
        self, examination_uuid: str, finding_uuid: str
    ) -> None:
        examination = self.get_patient_examination_by_uuid(examination_uuid)
        examination.delete_finding(finding_uuid)

    def delete_classification_choice_from_finding(
        self,
        examination_uuid: str,
        finding_uuid: str,
        choice_uuid: str,
    ) -> None:
        examination = self.get_patient_examination_by_uuid(examination_uuid)
        finding = examination.get_finding_by_uuid(finding_uuid)
        finding.delete_classification_choice(choice_uuid)

    def delete_indication_from_examination(
        self,
        examination_uuid: str,
        indication_uuid: str,
    ) -> None:
        examination = self.get_patient_examination_by_uuid(examination_uuid)
        examination.delete_indication(indication_uuid)
