"""Persisted examination alternatives and reproducible selected study records."""

from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from lx_dtypes.models.contracts.dtypes_record_persistence import (
    DtypesRecordPersistencePayload,
)
from lx_dtypes.models.ledger.medical.Write import (
    PatientLabValueCreate,
    PatientMedicationCreate,
)

PositiveId = Annotated[int, Field(gt=0)]


class RevisionContract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class ExaminationClinicalContent(RevisionContract):
    """Editable complete clinical snapshot, including repeated descriptors and values."""

    examination: DtypesRecordPersistencePayload
    medications: list[PatientMedicationCreate] = Field(default_factory=list)
    lab_values: list[PatientLabValueCreate] = Field(default_factory=list)


class ExaminationEvidenceSelection(RevisionContract):
    report_id: PositiveId | None = None
    video_id: PositiveId | None = None
    annotator: str | None = Field(default=None, min_length=1)
    medication_ids: list[PositiveId] = Field(default_factory=list)
    lab_value_ids: list[PositiveId] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_selection(self) -> Self:
        if self.annotator is not None and self.video_id is None:
            raise ValueError("annotator requires video_id")
        for ids in (self.medication_ids, self.lab_value_ids):
            if len(ids) != len(set(ids)):
                raise ValueError("selected record IDs must be unique")
        return self


class ExaminationAnnotationSnapshot(RevisionContract):
    annotation_id: PositiveId
    frame_id: PositiveId
    frame_number: int = Field(ge=0)
    presentation_timestamp: int
    stream_time_base_num: int = Field(gt=0)
    stream_time_base_den: int = Field(gt=0)
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    label_name: str = Field(min_length=1)
    value: bool
    float_value: float | None = None
    annotator: str
    information_source_id: PositiveId | None = None
    information_source_name: str | None = None
    model_meta_id: PositiveId | None = None


class ExaminationEvidence(RevisionContract):
    report_id: PositiveId | None = None
    report_version: PositiveId | None = None
    report_text: str | None = None
    report_template_name: str | None = None
    report_template_version: str | None = None
    report_template_hash: str | None = None
    video_id: PositiveId | None = None
    processed_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    table_import_ids: list[PositiveId] = Field(default_factory=list)
    medication_ids: list[PositiveId] = Field(default_factory=list)
    lab_value_ids: list[PositiveId] = Field(default_factory=list)
    annotations: list[ExaminationAnnotationSnapshot] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_provenance(self) -> Self:
        if (self.report_id is None) != (self.report_version is None):
            raise ValueError("report identity and version must be supplied together")
        if self.processed_sha256 is not None and self.video_id is None:
            raise ValueError("processed hash requires video identity")
        if self.annotations and self.video_id is None:
            raise ValueError("annotations require a video")
        if any(
            item.artifact_sha256 != self.processed_sha256 for item in self.annotations
        ):
            raise ValueError("annotations must belong to the selected media generation")
        ids = [item.annotation_id for item in self.annotations]
        if len(ids) != len(set(ids)):
            raise ValueError("annotation identities must be unique")
        return self


class ExaminationRevisionSnapshot(RevisionContract):
    schema_version: Literal["1.0"] = "1.0"
    content: ExaminationClinicalContent
    evidence: ExaminationEvidence


class ExaminationRevisionCreate(RevisionContract):
    patient_examination_id: PositiveId
    title: str = Field(min_length=1, max_length=255)
    selection: ExaminationEvidenceSelection = Field(
        default_factory=ExaminationEvidenceSelection
    )
    source_revision_id: PositiveId | None = None

    @model_validator(mode="after")
    def validate_source(self) -> Self:
        if self.source_revision_id is not None and self.selection.model_fields_set:
            raise ValueError("Copy a revision or capture source selections, not both")
        return self


class ExaminationRevisionUpdate(RevisionContract):
    expected_version: PositiveId
    title: str = Field(min_length=1, max_length=255)
    content: ExaminationClinicalContent


class ExaminationRevisionVersion(RevisionContract):
    expected_version: PositiveId


class CaseExaminationSelection(ExaminationRevisionVersion):
    revision_id: PositiveId


class CaseExaminationSelectionRead(RevisionContract):
    patient_examination_id: PositiveId
    revision_id: PositiveId


class CaseStudyExportSelection(RevisionContract):
    case_ids: list[str] = Field(min_length=1, max_length=1000)
    output: Literal["json", "xlsx"] = "xlsx"

    @model_validator(mode="after")
    def validate_cases(self) -> Self:
        self.case_ids = [str(UUID(value)) for value in self.case_ids]
        if len(self.case_ids) != len(set(self.case_ids)):
            raise ValueError("case_ids must be unique")
        return self


class ExaminationRevisionRead(RevisionContract):
    id: PositiveId
    patient_examination_id: PositiveId
    title: str
    version: PositiveId
    snapshot: ExaminationRevisionSnapshot
    finalized_at: AwareDatetime | None
    updated_at: AwareDatetime


class SelectedExaminationExport(RevisionContract):
    patient_examination_id: PositiveId
    revision_id: PositiveId
    revision_version: PositiveId
    finalized_at: AwareDatetime
    snapshot: ExaminationRevisionSnapshot


class SelectedCaseExport(RevisionContract):
    schema_version: Literal["2.0"] = "2.0"
    generated_at: AwareDatetime
    case_id: UUID
    patient_id: PositiveId
    center_key: str | None
    is_closed: bool
    examinations: list[SelectedExaminationExport] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_examinations(self) -> Self:
        ids = [item.patient_examination_id for item in self.examinations]
        if len(ids) != len(set(ids)):
            raise ValueError("An examination can appear only once per case export")
        return self
