from typing import Dict, List, Optional, Union

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import uuid_factory
from lx_dtypes.utils.mixins.base_model import AppBaseModel

from .patient_finding import PatientFinding


class PatientExamination(AppBaseModel):
    uuid: str = Field(default_factory=uuid_factory)
    patient_uuid: str
    examination_name: str
    examination_template: Optional[str] = None
    findings: List[PatientFinding]

    @classmethod
    def create(
        cls,
        patient_uuid: str,
        examination_name: str,
        examination_template: Optional[str] = None,
    ) -> "PatientExamination":
        """Factory method to create a PatientExamination instance.

        Args:
            patient_uuid (str): The UUID of the patient.
            examination_name (str): The name of the examination.
            examination_template (Optional[str]): The template used for the examination.

        Returns:
            PatientExamination: The created PatientExamination instance.
        """
        model_dict: Dict[str, Union[str, None, List[PatientFinding]]] = {
            "patient_uuid": patient_uuid,
            "examination_name": examination_name,
            "examination_template": examination_template,
            "findings": [],
        }
        instance = cls.model_validate(model_dict)
        return instance

    def create_finding(self, finding_name: str) -> PatientFinding:
        finding = PatientFinding.create(
            patient_uuid=self.patient_uuid,
            patient_examination_uuid=self.uuid,
            finding_name=finding_name,
        )
        self.findings.append(finding)
        return finding

    def get_finding_by_uuid(self, finding_uuid: str) -> PatientFinding:
        finding = next((f for f in self.findings if f.uuid == finding_uuid), None)
        if finding is None:
            raise ValueError(
                f"Finding with UUID {finding_uuid} not found in examination {self.uuid}."
            )
        return finding
