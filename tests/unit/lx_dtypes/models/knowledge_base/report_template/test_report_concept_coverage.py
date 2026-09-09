import pytest
from pydantic import ValidationError

from lx_dtypes import ReportConceptCoverage as ExportedReportConceptCoverage
from lx_dtypes.models.knowledge_base.report_template import (
    ReportConceptApplicability,
    ReportConceptCoverage,
    ReportConceptCoverageIdentity,
    ReportConceptCoverageItem,
    ReportConceptCoverageProvenance,
)


def _identity() -> ReportConceptCoverageIdentity:
    return ReportConceptCoverageIdentity(
        module_name="coloreg",
        module_version="2026.03.27",
        module_digest="d" * 64,
        template_name="colonoscopy",
        template_version="1.2.0",
        template_digest="a" * 64,
    )


def _coverage() -> ReportConceptCoverage:
    return ReportConceptCoverage(
        identity=_identity(),
        provenance=ReportConceptCoverageProvenance(
            resolver="lx_dtypes.report_coverage",
            resolver_version="1.0.0",
            evidence_digest="b" * 64,
        ),
        concepts=(
            ReportConceptCoverageItem(
                concept_id="polyp.size_mm",
                label="Polyp size",
                applicability=ReportConceptApplicability(status="required"),
                validation_status="present",
                evidence_path=("findings", "0", "classifications", "size_mm"),
            ),
        ),
    )


def test_report_concept_coverage_is_exported_and_round_trips() -> None:
    coverage = _coverage()
    assert ExportedReportConceptCoverage is ReportConceptCoverage
    assert coverage.model_dump()["contract_version"] == "report_concept_coverage_v1"
    assert coverage.concepts[0].concept_id == "polyp.size_mm"


def test_not_applicable_requires_undetermined_status_and_reason() -> None:
    with pytest.raises(ValidationError):
        ReportConceptCoverageItem(
            concept_id="exam.incomplete",
            label="Incomplete examination",
            applicability=ReportConceptApplicability(
                status="not_applicable", reason="Not relevant"
            ),
            validation_status="present",
            evidence_path=("examination", "completion"),
        )

    with pytest.raises(ValidationError):
        ReportConceptApplicability(status="conditional")


def test_coverage_rejects_invalid_digest_and_unknown_contract_version() -> None:
    with pytest.raises(ValidationError):
        ReportConceptCoverageIdentity(
            module_name="coloreg",
            module_version="2026.03.27",
            module_digest="d" * 64,
            template_name="colonoscopy",
            template_version="1.2.0",
            template_digest="not-a-digest",
        )
    with pytest.raises(ValidationError):
        ReportConceptCoverage.model_validate(
            {**_coverage().model_dump(), "contract_version": "v2"}
        )


def test_coverage_rejects_module_version_and_digest_mismatches() -> None:
    coverage = _coverage()
    with pytest.raises(ValueError, match="identity"):
        coverage.validate_compatibility(
            _identity().model_copy(update={"module_version": "2026.04.01"})
        )
    with pytest.raises(ValueError, match="identity"):
        coverage.validate_compatibility(
            _identity().model_copy(update={"template_digest": "c" * 64})
        )
