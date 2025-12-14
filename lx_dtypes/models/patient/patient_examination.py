from datetime import datetime
from typing import List, Optional, TypedDict

from pydantic import Field, field_serializer, field_validator

from lx_dtypes.utils.factories.field_defaults import (
    list_of_patient_finding_factory,
    list_of_patient_indication_factory,
    uuid_factory,
)
from lx_dtypes.utils.mixins.base_model import AppBaseModel

from .patient_finding import PatientFinding, PatientFindingDataDict
from .patient_indication import PatientIndication, PatientIndicationDataDict


class PatientExaminationShallowDataDict(TypedDict):
    uuid: str
    patient_uuid: str
    examination_name: str
    examination_template: Optional[str]
    date: Optional[str]
    findings_uuids: List[str]
    indications_uuids: List[str]


class PatientExaminationDataDict(TypedDict):
    uuid: str
    patient_uuid: str
    examination_name: str
    examination_template: Optional[str]
    date: Optional[str]
    findings: List[PatientFindingDataDict]
    indications: List[PatientIndicationDataDict]


class PatientExaminationShallow(AppBaseModel):
    """Shallow representation of a PatientExamination."""

    uuid: str = Field(default_factory=uuid_factory)
    patient_uuid: str
    examination_name: str
    examination_template: Optional[str] = None
    date: Optional[datetime] = None
    findings_uuids: List[str] = Field(default_factory=list)
    indications_uuids: List[str] = Field(default_factory=list)

    @field_validator("date", mode="before")
    def validate_date(cls, value: Optional[str]) -> Optional[datetime]:
        if value is None:
            return value
        return datetime.fromisoformat(value)

    @field_serializer("date")
    def serialize_date(self, date: Optional[datetime]) -> Optional[str]:
        if date is None:
            return None
        return date.isoformat()

    @property
    def ddict_shallow(self) -> type[PatientExaminationShallowDataDict]:
        return PatientExaminationShallowDataDict

    def to_ddict_shallow(self) -> PatientExaminationShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict


class PatientExamination(PatientExaminationShallow):
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

    findings: List[PatientFinding] = Field(
        default_factory=list_of_patient_finding_factory
    )

    indications: List[PatientIndication] = Field(
        default_factory=list_of_patient_indication_factory
    )

    @property
    def ddict(self) -> type[PatientExaminationDataDict]:
        return PatientExaminationDataDict

    @field_serializer("findings")
    def serialize_findings(
        self, findings: List[PatientFinding]
    ) -> List[PatientFindingDataDict]:
        return [finding.to_ddict() for finding in findings]

    @field_serializer("indications")
    def serialize_indications(
        self, indications: List[PatientIndication]
    ) -> List[PatientIndicationDataDict]:
        return [indication.to_ddict() for indication in indications]

    def to_ddict(self) -> PatientExaminationDataDict:
        data_dict = self.ddict(**self.model_dump())
        return data_dict

    def to_ddict_shallow(self) -> PatientExaminationShallowDataDict:
        findings_uuids = [finding.uuid for finding in self.findings]
        indications_uuids = [indication.uuid for indication in self.indications]
        data_dict = self.ddict_shallow(
            uuid=self.uuid,
            patient_uuid=self.patient_uuid,
            examination_name=self.examination_name,
            examination_template=self.examination_template,
            date=self.serialize_date(self.date),
            findings_uuids=findings_uuids,
            indications_uuids=indications_uuids,
        )
        return data_dict

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
        date_str = date.isoformat() if date else None
        model_dict = PatientExaminationDataDict(
            patient_uuid=patient_uuid,
            uuid=examination_uuid if examination_uuid else uuid_factory(),
            examination_name=examination_name,
            examination_template=examination_template,
            date=date_str,
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
