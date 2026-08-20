from __future__ import annotations

import pytest
from pydantic import ValidationError

from lx_dtypes.models.knowledge_base.report_template.ClassificationValidator import (
    ClassificationValidator,
)


def test_classification_validator_defaults_query_from_top_level_fields() -> None:
    validator = ClassificationValidator.model_validate(
        {
            "name": "size_required",
            "finding": "esophagus_polyp",
            "classification": "size_mm",
        }
    )

    assert validator.operator == "exists"
    assert validator.precedence == "required"
    assert validator.query.finding == "esophagus_polyp"
    assert validator.query.classification == "size_mm"


def test_classification_validator_backfills_top_level_fields_from_query() -> None:
    validator = ClassificationValidator.model_validate(
        {
            "name": "size_absent",
            "precedence": "optional",
            "query": {
                "finding": "esophagus_polyp",
                "classification": "size_mm",
                "operator": "missing",
            },
        }
    )

    assert validator.finding == "esophagus_polyp"
    assert validator.classification == "size_mm"
    assert validator.operator == "missing"
    assert validator.precedence == "optional"


def test_classification_validator_rejects_unknown_operator() -> None:
    with pytest.raises(ValidationError):
        ClassificationValidator.model_validate(
            {
                "name": "size_invalid",
                "finding": "esophagus_polyp",
                "classification": "size_mm",
                "operator": "asd",
            }
        )


def test_classification_validator_requires_condition_block() -> None:
    with pytest.raises(ValidationError, match="requires a populated `condition` block"):
        ClassificationValidator.model_validate(
            {
                "name": "size_conditional",
                "finding": "esophagus_polyp",
                "classification": "size_cat",
                "operator": "condition",
                "query": {
                    "finding": "esophagus_polyp",
                    "classification": "size_cat",
                    "operator": "condition",
                },
            }
        )
