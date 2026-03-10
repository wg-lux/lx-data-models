from __future__ import annotations

import pytest
from pydantic import ValidationError

from lx_dtypes.models.knowledge_base.report_template.FindingsValidator import (
    FindingsValidator,
)


def test_findings_validator_defaults_query_from_top_level_fields() -> None:
    validator = FindingsValidator.model_validate(
        {
            "name": "f_validator",
            "finding": "esophagus_polyp",
        }
    )

    assert validator.operator == "exists"
    assert validator.query.operator == "exists"
    assert validator.query.finding == "esophagus_polyp"
    assert validator.query.condition is None


def test_findings_validator_backfills_top_level_fields_from_query() -> None:
    validator = FindingsValidator.model_validate(
        {
            "name": "f_validator",
            "query": {
                "finding": "esophagus_polyp",
                "operator": "missing",
            },
        }
    )

    assert validator.finding == "esophagus_polyp"
    assert validator.operator == "missing"
    assert validator.query.finding == "esophagus_polyp"
    assert validator.query.operator == "missing"


def test_findings_validator_rejects_unknown_operator() -> None:
    with pytest.raises(ValidationError):
        FindingsValidator.model_validate(
            {
                "name": "f_validator",
                "finding": "esophagus_polyp",
                "operator": "ASD",
            }
        )


def test_findings_validator_rejects_mismatched_query_and_top_level_operator() -> None:
    with pytest.raises(ValidationError, match="query.operator must match"):
        FindingsValidator.model_validate(
            {
                "name": "f_validator",
                "finding": "esophagus_polyp",
                "operator": "missing",
                "query": {
                    "finding": "esophagus_polyp",
                    "operator": "exists",
                },
            }
        )


def test_findings_validator_conditional_requires_condition_block() -> None:
    with pytest.raises(ValidationError, match="requires a populated `condition` block"):
        FindingsValidator.model_validate(
            {
                "name": "f_validator",
                "finding": "esophagus_polyp",
                "operator": "conditional",
                "query": {
                    "finding": "esophagus_polyp",
                    "operator": "conditional",
                },
            }
        )


def test_findings_validator_conditional_accepts_condition_clauses() -> None:
    validator = FindingsValidator.model_validate(
        {
            "name": "polyp_has_lst_if_large",
            "finding": "esophagus_polyp",
            "operator": "conditional",
            "query": {
                "finding": "esophagus_polyp",
                "operator": "conditional",
                "condition": {
                    "any": [
                        {
                            "classification": "size_mm",
                            "comparator": "gt",
                            "value": 10,
                        },
                        {
                            "classification": "size_cat",
                            "comparator": "eq",
                            "value": "large",
                        },
                    ],
                    "then_requires": [
                        {"classification": "lst"},
                    ],
                },
            },
        }
    )

    assert validator.query.operator == "conditional"
    assert validator.query.condition is not None
    assert len(validator.query.condition.any) == 2
    assert validator.query.condition.any[0].comparator == "gt"
    assert len(validator.query.condition.then_requires) == 1
    assert validator.query.condition.then_requires[0].classification == "lst"


def test_findings_validator_rejects_condition_for_non_conditional_operators() -> None:
    with pytest.raises(ValidationError, match="does not allow a `condition` block"):
        FindingsValidator.model_validate(
            {
                "name": "f_validator",
                "finding": "esophagus_polyp",
                "operator": "exists",
                "query": {
                    "finding": "esophagus_polyp",
                    "operator": "exists",
                    "condition": {
                        "any": [
                            {
                                "classification": "size_mm",
                                "comparator": "gt",
                                "value": 10,
                            }
                        ]
                    },
                },
            }
        )


def test_findings_validator_enforces_clause_payload_for_comparators() -> None:
    with pytest.raises(ValidationError, match="requires `value`"):
        FindingsValidator.model_validate(
            {
                "name": "f_validator",
                "finding": "esophagus_polyp",
                "operator": "conditional",
                "query": {
                    "finding": "esophagus_polyp",
                    "operator": "conditional",
                    "condition": {
                        "all": [
                            {
                                "classification": "size_mm",
                                "comparator": "gt",
                            }
                        ]
                    },
                },
            }
        )

    validator = FindingsValidator.model_validate(
        {
            "name": "f_validator",
            "finding": "esophagus_polyp",
            "operator": "conditional",
            "query": {
                "finding": "esophagus_polyp",
                "operator": "conditional",
                "condition": {
                    "all": [
                        {
                            "classification": "size_cat",
                            "comparator": "in",
                            "values": ["large", "xlarge"],
                        }
                    ]
                },
            },
        }
    )
    assert validator.query.condition is not None
    assert validator.query.condition.all[0].values == ["large", "xlarge"]
