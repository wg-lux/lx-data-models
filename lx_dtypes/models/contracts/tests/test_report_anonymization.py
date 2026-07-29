from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts import (
    ReportAnonymizationRequestV2 as ExportedReportAnonymizationRequestV2,
)
from lx_dtypes.models.contracts.report_anonymization import (
    ReportAnonymizationErrorCode,
    ReportAnonymizationFailureV2,
    ReportAnonymizationPhase,
    ReportAnonymizationProvenanceV2,
    ReportAnonymizationRequestV2,
    ReportAnonymizationResultV2,
    ReportArtifactValidationV2,
)
from lx_dtypes.models.meta.SensitiveMeta import SensitiveMeta


def _request(source: Path, output_directory: Path) -> ReportAnonymizationRequestV2:
    content = source.read_bytes()
    return ReportAnonymizationRequestV2(
        attempt_id=uuid4(),
        source_path=source,
        source_sha256=hashlib.sha256(content).hexdigest(),
        source_size_bytes=len(content),
        output_directory=output_directory,
        deadline_monotonic_ns=10,
    )


def test_report_v2_request_rejects_unknown_fields_and_nonpositive_deadline(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.pdf"
    output_directory = tmp_path / "attempt"
    source.write_bytes(b"%PDF-1.4\n%%EOF\n")
    output_directory.mkdir()
    request = _request(source, output_directory)

    with pytest.raises(ValidationError):
        ReportAnonymizationRequestV2.model_validate(
            {
                **request.model_dump(),
                "deadline_monotonic_ns": 0,
                "unexpected": True,
            }
        )


def test_report_v2_contract_rejects_unknown_version_and_is_exported(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.pdf"
    output_directory = tmp_path / "attempt"
    source.write_bytes(b"%PDF-1.4\n%%EOF\n")
    output_directory.mkdir()
    request = _request(source, output_directory)

    assert ExportedReportAnonymizationRequestV2 is ReportAnonymizationRequestV2
    with pytest.raises(ValidationError):
        ReportAnonymizationRequestV2.model_validate(
            {
                **request.model_dump(),
                "contract_version": "report_anonymization_v3",
            }
        )


def test_report_v2_request_rejects_symlink_source(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    linked_source = tmp_path / "linked.pdf"
    output_directory = tmp_path / "attempt"
    source.write_bytes(b"%PDF-1.4\n%%EOF\n")
    linked_source.symlink_to(source)
    output_directory.mkdir()

    with pytest.raises(ValidationError, match="non-symlink"):
        _request(linked_source, output_directory)


def test_report_v2_result_round_trips_as_json(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.pdf"
    artifact.write_bytes(b"%PDF-1.4\n%%EOF\n")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    result = ReportAnonymizationResultV2(
        attempt_id=uuid4(),
        source_sha256="a" * 64,
        original_text="original",
        anonymized_text="anonymized",
        extracted_metadata=SensitiveMeta(first_name="ANON", last_name="ANON"),
        artifact_path=artifact,
        artifact_sha256=digest,
        artifact_size_bytes=artifact.stat().st_size,
        artifact_validation=ReportArtifactValidationV2(
            page_count=1,
            repaired=False,
        ),
        provenance=ReportAnonymizationProvenanceV2(
            anonymizer_version="0.9.3.4",
            detector_sources=("spacy",),
            model_names=("de_core_news_lg",),
            model_versions={"de_core_news_lg": "3.8"},
            proposal_counts={"person": 2},
            used_llm=False,
            deterministic=True,
        ),
    )

    restored = ReportAnonymizationResultV2.model_validate_json(result.model_dump_json())

    assert restored == result
    assert restored.extracted_metadata.first_name == "ANON"
    assert restored.artifact_validation.validator == "pymupdf_full_parse_v1"


def test_report_v2_failure_is_machine_safe_and_strict() -> None:
    failure = ReportAnonymizationFailureV2(
        attempt_id=uuid4(),
        phase=ReportAnonymizationPhase.VALIDATE_ARTIFACT,
        error_code=ReportAnonymizationErrorCode.VALIDATION_FAILED,
        retryable=False,
    )

    assert "detail" not in failure.model_dump()
    with pytest.raises(ValidationError):
        ReportAnonymizationFailureV2.model_validate(
            {**failure.model_dump(), "retryable": "false"}
        )
