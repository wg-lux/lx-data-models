"""Versioned contract describing which report concepts a template covers.

Coverage results are immutable and carry digests of the module, template, and
evidence they were derived from, so consumers can detect stale results.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from lx_dtypes.models.model import FrozenContractModel

#: Version tag of the coverage contract; bumped on incompatible changes.
ReportConceptCoverageContractVersion = Literal["report_concept_coverage_v1"]
REPORT_CONCEPT_COVERAGE_CONTRACT_VERSION: ReportConceptCoverageContractVersion = (
    "report_concept_coverage_v1"
)
#: Whether a concept applies to a report.
ReportConceptApplicabilityStatus = Literal[
    "required", "conditional", "not_applicable", "unknown"
]
#: Whether captured data satisfies a concept. ``undetermined`` is used for
#: concepts that do not apply.
ReportConceptValidationStatus = Literal[
    "present", "missing", "invalid", "unknown", "undetermined"
]


class ReportConceptCoverageIdentity(FrozenContractModel):
    """Immutable identity of the module and template that produced coverage."""

    module_name: str = Field(min_length=1)
    module_version: str = Field(min_length=1)
    module_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    template_name: str = Field(min_length=1)
    template_version: str = Field(min_length=1)
    template_digest: str = Field(pattern=r"^[0-9a-f]{64}$")


class ReportConceptCoverageProvenance(FrozenContractModel):
    """Tool and evidence that produced a coverage result.

    Attributes:
        resolver: Name of the component that computed the coverage.
        resolver_version: Version of that component.
        evidence_digest: SHA-256 hex digest of the evidence that was evaluated.
    """

    resolver: str = Field(min_length=1)
    resolver_version: str = Field(min_length=1)
    evidence_digest: str = Field(pattern=r"^[0-9a-f]{64}$")


class ReportConceptApplicability(FrozenContractModel):
    """Whether a concept applies to a report, and why.

    A ``conditional`` status must name the ``rule`` that decides it, and a
    ``not_applicable`` status must give a ``reason``.
    """

    status: ReportConceptApplicabilityStatus
    rule: str | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def validate_conditional_rule(self) -> ReportConceptApplicability:
        """Require a rule for conditional and a reason for not-applicable concepts."""
        if self.status == "conditional" and not self.rule:
            raise ValueError("conditional applicability requires a rule")
        if self.status == "not_applicable" and not self.reason:
            raise ValueError("not_applicable applicability requires a reason")
        return self


class ReportConceptCoverageItem(FrozenContractModel):
    """Coverage status of one concept within a report template.

    Attributes:
        concept_id: Stable lowercase identifier of the concept.
        label: Human-readable concept label.
        applicability: Whether the concept applies to the report.
        validation_status: Whether captured data satisfies the concept.
        evidence_path: Primary path to the data that provides evidence.
        evidence_paths: Additional evidence paths, if any.
        guideline_citations: Guideline sections that require the concept.
    """

    concept_id: str = Field(pattern=r"^[a-z][a-z0-9_.:-]*$")
    label: str = Field(min_length=1)
    applicability: ReportConceptApplicability
    validation_status: ReportConceptValidationStatus
    evidence_path: tuple[str, ...] = Field(min_length=1)
    evidence_paths: tuple[tuple[str, ...], ...] = ()
    guideline_citations: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_status(self) -> ReportConceptCoverageItem:
        """Require ``undetermined`` validation for not-applicable concepts."""
        if (
            self.applicability.status == "not_applicable"
            and self.validation_status != "undetermined"
        ):
            raise ValueError(
                "not_applicable concepts must use the undetermined validation status"
            )
        return self


class ReportConceptCoverage(FrozenContractModel):
    """Versioned, reproducible technical coverage for one report template."""

    contract_version: ReportConceptCoverageContractVersion = (
        REPORT_CONCEPT_COVERAGE_CONTRACT_VERSION
    )
    identity: ReportConceptCoverageIdentity
    provenance: ReportConceptCoverageProvenance
    concepts: tuple[ReportConceptCoverageItem, ...] = ()

    def validate_compatibility(
        self, expected_identity: ReportConceptCoverageIdentity
    ) -> None:
        """Check that this coverage belongs to ``expected_identity``.

        Raises:
            ValueError: If the module, template version, or digests differ.
        """
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
