from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from pydantic import Field, field_serializer

from lx_dtypes.utils.factories.field_defaults import (
    list_of_patient_finding_factory,
    list_of_patient_indication_factory,
    uuid_factory,
)
from lx_dtypes.utils.mixins.base_model import AppBaseModel

from .patient_finding import PatientFinding
from .patient_indication import PatientIndication


class PatientExaminationDataDict(TypedDict):
    uuid: str
    patient_uuid: str
    examination_name: str
    examination_template: Optional[str]
    date: Optional[datetime]
    findings: List[PatientFinding]
    indications: List[PatientIndication]


class PatientExamination(AppBaseModel):
    """
    Represents a patient's examination, including findings and indications.

    Attributes:
        uuid (str): Unique identifier for the patient examination.
        patient_uuid (str): Unique identifier for the patient.
        date (datetime | None): Date of the examination (if multiple, day of the examination start).
        examination_name (str): Name of the examination.
        examination_template (str | None): Template used for the examination.
        findings (list[PatientFinding]): List of findings associated with the examination.
        indications (list[PatientIndication]): List of indications associated with the examination.
    """

    uuid: str = Field(default_factory=uuid_factory)
    patient_uuid: str
    date: Optional[datetime] = None
    examination_name: str
    examination_template: Optional[str] = None
    findings: List[PatientFinding] = Field(
        default_factory=list_of_patient_finding_factory
    )
    indications: List[PatientIndication] = Field(
        default_factory=list_of_patient_indication_factory
    )

    @field_serializer("findings")
    def serialize_findings(
        self, findings: List[PatientFinding]
    ) -> List[Dict[str, Any]]:
        return [finding.model_dump() for finding in findings]

    @field_serializer("indications")
    def serialize_indications(
        self, indications: List[PatientIndication]
    ) -> List[Dict[str, Any]]:
        return [indication.model_dump() for indication in indications]

    @classmethod
    def create(
        cls,
        patient_uuid: str,
        examination_name: str,
        examination_uuid: Optional[str] = None,
        examination_template: Optional[str] = None,
        date: Optional[datetime] = None,
    ) -> "PatientExamination":
        """Factory method to create a PatientExamination instance.

        Args:
            patient_uuid (str): The UUID of the patient.
            examination_name (str): The name of the examination.
            examination_template (Optional[str]): The template used for the examination.
            date (Optional[datetime]): The date of the examination.
            examination_uuid (Optional[str]): The UUID of the examination.

        Returns:
            PatientExamination: The created PatientExamination instance.
        """
        model_dict = PatientExaminationDataDict(
            patient_uuid=patient_uuid,
            uuid=examination_uuid if examination_uuid else uuid_factory(),
            examination_name=examination_name,
            examination_template=examination_template,
            date=date,
            findings=[],
            indications=[],
        )
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

    def delete_finding(self, finding_uuid: str) -> None:
        finding = self.get_finding_by_uuid(finding_uuid)
        self.findings.remove(finding)

    def create_indication(self, indication_name: str) -> PatientIndication:
        indication = PatientIndication.create(
            patient_uuid=self.patient_uuid,
            indication_name=indication_name,
        )
        self.indications.append(indication)
        return indication

    def get_indication_by_uuid(self, indication_uuid: str) -> PatientIndication:
        indication = next(
            (i for i in self.indications if i.uuid == indication_uuid), None
        )
        if indication is None:
            raise ValueError(
                f"Indication with UUID {indication_uuid} not found in examination {self.uuid}."
            )
        return indication

    def delete_indication(self, indication_uuid: str) -> None:
        indication = self.get_indication_by_uuid(indication_uuid)
        self.indications.remove(indication)
