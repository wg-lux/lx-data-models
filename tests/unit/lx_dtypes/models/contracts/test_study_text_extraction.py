from uuid import uuid4

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.study_text_extraction import (
    StudyFindingApprovalRequest,
    StudyTextExtractionEvidence,
)


def test_approval_request_accepts_json_uuid_and_rejects_unknown_fields():
    instance = uuid4()
    request = StudyFindingApprovalRequest.model_validate(
        {"report": 1, "instance": str(instance), "classifications": []}
    )
    assert request.instance == instance
    with pytest.raises(ValidationError):
        StudyFindingApprovalRequest.model_validate(
            {"report": 1, "instance": str(instance), "source": "manual"}
        )


def test_evidence_requires_definition_digest_and_ordered_spans():
    base = {
        "knowledge_base_module": "coloreg",
        "knowledge_base_version": "0.2.0",
        "cohort_definition_sha256": "a" * 64,
        "mentions": [
            {"finding": "polyp", "presence": "present", "start": 0, "end": 5}
        ],
    }
    assert StudyTextExtractionEvidence.model_validate(base).classification_mentions == []
    with pytest.raises(ValidationError):
        StudyTextExtractionEvidence.model_validate(
            {**base, "cohort_definition_sha256": "not-a-digest"}
        )
    with pytest.raises(ValidationError):
        StudyTextExtractionEvidence.model_validate(
            {
                **base,
                "classification_mentions": [
                    {
                        "finding": "polyp",
                        "classification": "c",
                        "choice": "x",
                        "start": 4,
                        "end": 4,
                    }
                ],
            }
        )
