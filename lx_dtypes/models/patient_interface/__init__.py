from lx_dtypes.models.knowledge_base import KnowledgeBase
from lx_dtypes.models.patient.patient_examination import PatientExamination
from lx_dtypes.models.patient.patient_finding import PatientFinding
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
