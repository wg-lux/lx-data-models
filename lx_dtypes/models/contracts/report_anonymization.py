from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from lx_dtypes.models.meta.SensitiveMeta import SensitiveMeta

ReportAnonymizationContractVersion = Literal["report_anonymization"]
REPORT_ANONYMIZATION_CONTRACT_VERSION: ReportAnonymizationContractVersion = (
    "report_anonymization"
)


class ReportAnonymizationPhase(StrEnum):
    VALIDATE_REQUEST = "validate_request"
    EXTRACT_TEXT = "extract_text"
    EXTRACT_METADATA = "extract_metadata"
    ANONYMIZE_TEXT = "anonymize_text"
    WRITE_ARTIFACT = "write_artifact"
    VALIDATE_ARTIFACT = "validate_artifact"


class ReportAnonymizationWarningCode(StrEnum):
    NONDETERMINISTIC_PROVIDER = "nondeterministic_provider"
    PDF_REPAIRED = "pdf_repaired"


class ReportAnonymizationErrorCode(StrEnum):
    INVALID_CONTRACT = "invalid_contract"
    SOURCE_IDENTITY_MISMATCH = "source_identity_mismatch"
    UNSUPPORTED_DOCUMENT = "unsupported_document"
    RESOURCE_LIMIT = "resource_limit"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    VALIDATION_FAILED = "validation_failed"
    ARTIFACT_EXISTS = "artifact_exists"
    DEADLINE_EXCEEDED = "deadline_exceeded"
    CANCELLED = "cancelled"


class ReportAnonymizationOptions(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    use_ensemble: bool = False
    verbose: bool = True
    use_llm: bool | None = None


class ReportAnonymizationRequest(BaseModel):
    """One immutable local report snapshot assigned to one host-owned attempt."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    contract_version: ReportAnonymizationContractVersion = (
        REPORT_ANONYMIZATION_CONTRACT_VERSION
    )
    attempt_id: UUID
    source_path: Path
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_size_bytes: int = Field(gt=0)
    output_directory: Path
    create_anonymized_pdf: Literal[True] = True
    deadline_monotonic_ns: int | None = Field(default=None, gt=0)
    options: ReportAnonymizationOptions = Field(
        default_factory=ReportAnonymizationOptions
    )

    @model_validator(mode="after")
    def validate_local_paths(self) -> ReportAnonymizationRequest:
        if self.source_path.is_symlink() or not self.source_path.is_file():
            raise ValueError("source_path must be a regular non-symlink file")
        if self.output_directory.is_symlink() or not self.output_directory.is_dir():
            raise ValueError(
                "output_directory must be an existing non-symlink directory"
            )
        if self.source_path.resolve() == self.output_directory.resolve():
            raise ValueError("source_path and output_directory must be different")
        return self


class ReportAnonymizationProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    contract_version: ReportAnonymizationContractVersion = (
        REPORT_ANONYMIZATION_CONTRACT_VERSION
    )
    implementation: Literal["lx_anonymizer.ReportReader"] = "lx_anonymizer.ReportReader"
    anonymizer_version: str = Field(min_length=1)
    detector_sources: tuple[str, ...] = ()
    model_names: tuple[str, ...] = ()
    model_versions: dict[str, str] = Field(default_factory=dict)
    proposal_counts: dict[str, int] = Field(default_factory=dict)
    used_llm: bool
    deterministic: bool

    @field_validator("anonymizer_version")
    @classmethod
    def validate_anonymizer_version(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("anonymizer_version must not be blank")
        return value

    @field_validator("detector_sources", "model_names")
    @classmethod
    def validate_names(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not item.strip() for item in value):
            raise ValueError("provenance names must not contain blank values")
        return value

    @field_validator("model_versions")
    @classmethod
    def validate_model_versions(cls, value: dict[str, str]) -> dict[str, str]:
        if any(not key.strip() or not item.strip() for key, item in value.items()):
            raise ValueError("model_versions keys and values must not be blank")
        return value

    @field_validator("proposal_counts")
    @classmethod
    def validate_proposal_counts(cls, value: dict[str, int]) -> dict[str, int]:
        if any(not key.strip() or count < 0 for key, count in value.items()):
            raise ValueError(
                "proposal_counts requires non-blank keys and non-negative counts"
            )
        return value


class ReportArtifactValidation(BaseModel):
    """Evidence that the closed attempt artifact passed a full parser traversal."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    validator: Literal["pymupdf_full_parse_v1"] = "pymupdf_full_parse_v1"
    page_count: int = Field(gt=0)
    encrypted: Literal[False] = False
    repaired: bool


class ReportAnonymizationWarning(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    code: ReportAnonymizationWarningCode
    phase: ReportAnonymizationPhase


class ReportAnonymizationResult(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=False,
    )

    contract_version: ReportAnonymizationContractVersion = (
        REPORT_ANONYMIZATION_CONTRACT_VERSION
    )
    attempt_id: UUID
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    original_text: str
    anonymized_text: str
    extracted_metadata: SensitiveMeta
    artifact_path: Path
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    artifact_size_bytes: int = Field(gt=0)
    artifact_validation: ReportArtifactValidation
    provenance: ReportAnonymizationProvenance
    warnings: tuple[ReportAnonymizationWarning, ...] = ()


class ReportAnonymizationFailure(BaseModel):
    """Machine-safe failure classification returned across integration boundaries."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    contract_version: ReportAnonymizationContractVersion = (
        REPORT_ANONYMIZATION_CONTRACT_VERSION
    )
    attempt_id: UUID
    phase: ReportAnonymizationPhase
    error_code: ReportAnonymizationErrorCode
    retryable: bool


__all__ = [
    "REPORT_ANONYMIZATION_CONTRACT_VERSION",
    "ReportAnonymizationContractVersion",
    "ReportAnonymizationErrorCode",
    "ReportAnonymizationFailure",
    "ReportAnonymizationOptions",
    "ReportAnonymizationPhase",
    "ReportAnonymizationProvenance",
    "ReportAnonymizationRequest",
    "ReportAnonymizationResult",
    "ReportAnonymizationWarning",
    "ReportAnonymizationWarningCode",
    "ReportArtifactValidation",
]
