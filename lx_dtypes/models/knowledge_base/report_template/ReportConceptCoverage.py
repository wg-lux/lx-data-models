from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


REPORT_CONCEPT_COVERAGE_CONTRACT_VERSION = "report_concept_coverage_v1"
ReportConceptCoverageContractVersion = Literal["report_concept_coverage_v1"]
ReportConceptApplicabilityStatus = Literal[
    "required", "conditional", "not_applicable", "unknown"
]
ReportConceptValidationStatus = Literal[
    "present", "missing", "invalid", "unknown", "undetermined"
]


class ReportConceptCoverageIdentity(BaseModel):
    """Immutable identity of the module and template that produced coverage."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    module_name: str = Field(min_length=1)
    module_version: str = Field(min_length=1)
    module_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    template_name: str = Field(min_length=1)
    template_version: str = Field(min_length=1)
    template_digest: str = Field(pattern=r"^[0-9a-f]{64}$")


class ReportConceptCoverageProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    resolver: str = Field(min_length=1)
    resolver_version: str = Field(min_length=1)
    evidence_digest: str = Field(pattern=r"^[0-9a-f]{64}$")


class ReportConceptApplicability(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    status: ReportConceptApplicabilityStatus
    rule: str | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def validate_conditional_rule(self) -> "ReportConceptApplicability":
        if self.status == "conditional" and not self.rule:
            raise ValueError("conditional applicability requires a rule")
        if self.status == "not_applicable" and not self.reason:
            raise ValueError("not_applicable applicability requires a reason")
        return self


class ReportConceptCoverageItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    concept_id: str = Field(pattern=r"^[a-z][a-z0-9_.:-]*$")
    label: str = Field(min_length=1)
    applicability: ReportConceptApplicability
    validation_status: ReportConceptValidationStatus
    evidence_path: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_status(self) -> "ReportConceptCoverageItem":
        if (
            self.applicability.status == "not_applicable"
            and self.validation_status != "undetermined"
        ):
            raise ValueError(
                "not_applicable concepts must use the undetermined validation status"
            )
        return self


class ReportConceptCoverage(BaseModel):
    """Versioned, reproducible technical coverage for one report template."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    contract_version: ReportConceptCoverageContractVersion = (
        REPORT_CONCEPT_COVERAGE_CONTRACT_VERSION
    )
    identity: ReportConceptCoverageIdentity
    provenance: ReportConceptCoverageProvenance
    concepts: tuple[ReportConceptCoverageItem, ...] = ()

    def validate_compatibility(
        self, expected_identity: ReportConceptCoverageIdentity
    ) -> None:
        if self.identity != expected_identity:
            raise ValueError(
                "report concept coverage identity does not match the expected "
                "module, template version, or digest"
            )


__all__ = [
    "REPORT_CONCEPT_COVERAGE_CONTRACT_VERSION",
    "ReportConceptApplicability",
    "ReportConceptApplicabilityStatus",
    "ReportConceptCoverage",
    "ReportConceptCoverageContractVersion",
    "ReportConceptCoverageIdentity",
    "ReportConceptCoverageItem",
    "ReportConceptCoverageProvenance",
    "ReportConceptValidationStatus",
]
