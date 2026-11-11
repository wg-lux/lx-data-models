from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import Field

from lx_dtypes.models.model import FrozenContractModel

AnonymizationQualityMediaType = Literal["video", "pdf"]


class SensitiveMetaHandlingPolicy(StrEnum):
    RETAIN_FOR_GOVERNANCE = "retain_for_governance"
    CLEAR_DIRECT_IDENTIFIERS = "clear_direct_identifiers"
    DELETE_SENSITIVE_META = "delete_sensitive_meta"


class QualityEvaluationStatus(StrEnum):
    PASSED = "passed"
    RESIDUAL_PHI_DETECTED = "residual_phi_detected"
    NOT_VALIDATED = "not_validated"
    FAILED_OR_LOST = "failed_or_lost"
    NO_SENSITIVE_META = "no_sensitive_meta"
    NOT_MEASURABLE = "not_measurable"


class AnonymizationQualityResult(FrozenContractModel):
    media_type: AnonymizationQualityMediaType
    media_id: int
    status: str
    residual_phi_detected: bool
    checked_fields: list[str] = Field(default_factory=list)
    leaked_field_count: int = 0
    missing_sensitive_meta_deletion_count: int = 0
    raw_artifact_residual_count: int = 0
    processed_artifact_sha256: str = ""
    warnings: list[str] = Field(default_factory=list)


class AnonymizationQualitySummary(FrozenContractModel):
    total: int
    residual_phi_detected_count: int
    leaked_field_count: int
    missing_sensitive_meta_deletion_count: int
    raw_artifact_residual_count: int
    status_counts: dict[str, int]


class AnonymizationQualityPayload(FrozenContractModel):
    schema_version: str = "1.0"
    sensitive_meta_policy: SensitiveMetaHandlingPolicy
    policy_applied: bool
    summary: AnonymizationQualitySummary
    results: list[AnonymizationQualityResult]


__all__ = [
    "AnonymizationQualityMediaType",
    "AnonymizationQualityPayload",
    "AnonymizationQualityResult",
    "AnonymizationQualitySummary",
    "QualityEvaluationStatus",
    "SensitiveMetaHandlingPolicy",
]
