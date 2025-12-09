from lx_dtypes.models.knowledge_base import KnowledgeBase
from lx_dtypes.models.patient.patient_examination import PatientExamination
from lx_dtypes.models.patient.patient_finding import PatientFinding
from lx_dtypes.models.patient.patient_finding_classification_choice import (
    PatientFindingClassificationChoice,
)
from lx_dtypes.models.patient.patient_ledger import PatientLedger
from lx_dtypes.utils.mixins.base_model import AppBaseModel


class PatientInterface(AppBaseModel):
    knowledge_base: KnowledgeBase
    patient_ledger: PatientLedger

    def get_patient_by_uuid(self, patient_uuid: str):
        patient = self.patient_ledger.get_patient_by_uuid(patient_uuid)
        return patient

    def _examination_exists(self, examination_name: str) -> bool:
        try:
            self.knowledge_base.get_examination(examination_name)
            return True
        except KeyError:
            return False

    def _finding_exists(self, finding_name: str) -> bool:
        try:
            self.knowledge_base.get_finding(finding_name)
            return True
        except KeyError:
            return False

    def _classification_exists(self, classification_name: str) -> bool:
        try:
            self.knowledge_base.get_classification(classification_name)
            return True
        except KeyError:
            return False

    def _classification_choice_exists(self, choice_name: str) -> bool:
        try:
            self.knowledge_base.get_classification_choice(choice_name)
            return True
        except KeyError:
            return False

    def create_patient_examination(self, patient_uuid: str, examination_name: str):
        if not self._examination_exists(examination_name):
            raise ValueError(
                f"Examination '{examination_name}' does not exist in the knowledge base."
            )

        examination = PatientExamination.create(
            patient_uuid=patient_uuid,
            examination_name=examination_name,
            examination_template=None,
        )

        self.patient_ledger.add_patient_examination(examination)
        return examination

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

    def create_examination_finding(self, examination_uuid: str, finding_name: str):
        examination = self.get_patient_examination_by_uuid(examination_uuid)
        if not self._finding_exists(finding_name):
            raise ValueError(
                f"Finding '{finding_name}' does not exist in the knowledge base."
            )

        finding = examination.create_finding(finding_name)
        return finding

    def add_classification_choice_to_finding(
        self,
        examination_uuid: str,
        finding_uuid: str,
        classification_name: str,
        choice_name: str,
    ):
        if not self._classification_exists(classification_name):
            raise ValueError(
                f"Classification '{classification_name}' does not exist in the knowledge base."
            )

        if not self._classification_choice_exists(choice_name):
            raise ValueError(
                f"Classification choice '{choice_name}' does not exist in the knowledge base."
            )

        classification_object = self.knowledge_base.get_classification(
            classification_name
        )
        valid_choices = classification_object.choice_names

        if choice_name not in valid_choices:
            raise ValueError(
                f"Choice '{choice_name}' is not a valid choice for classification '{classification_name}'. Valid choices are: {valid_choices}"
            )

        patient_finding = (
            self.get_patient_finding_by_patient_examination_and_finding_uuid(
                examination_uuid, finding_uuid
            )
        )

        patient_finding_classifications = (
            patient_finding.get_or_create_classifications()
        )

        classification_choice = PatientFindingClassificationChoice.create(
            choice_name=choice_name,
            patient_uuid=patient_finding.patient_uuid,
            patient_examination_uuid=patient_finding.patient_examination_uuid,
            patient_finding_uuid=patient_finding.uuid,
            patient_finding_classifications_uuid=patient_finding_classifications.uuid,
            classification_name=classification_name,
        )
        patient_finding.add_classification_choice(classification_choice)
