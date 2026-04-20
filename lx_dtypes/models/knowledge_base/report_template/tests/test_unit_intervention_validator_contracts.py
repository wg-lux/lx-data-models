from __future__ import annotations

from lx_dtypes.models.knowledge_base.report_template.InterventionValidator import (
    InterventionValidator,
)
from lx_dtypes.models.knowledge_base.report_template.UnitValidator import UnitValidator


def test_unit_validator_accepts_condition_with_typed_requirement_reference() -> None:
    validator = UnitValidator.model_validate(
        {
            "name": "size_mm_requires_mm_unit",
            "finding": "esophagus_polyp",
            "classification": "size_mm",
            "unit": "millimeter",
            "operator": "condition",
            "query": {
                "finding": "esophagus_polyp",
                "classification": "size_mm",
                "unit": "millimeter",
                "operator": "condition",
                "condition": {
                    "all": [
                        {
                            "classification": "size_mm",
                            "comparator": "gt",
                            "value": 0,
                        }
                    ],
                    "then_requires": [
                        {
                            "kind": "unit",
                            "name": "millimeter",
                            "classification": "size_mm",
                        }
                    ],
                },
            },
        }
    )

    assert validator.query.condition is not None
    assert validator.query.condition.then_requires[0].kind == "unit"


def test_intervention_validator_accepts_condition() -> None:
    validator = InterventionValidator.model_validate(
        {
            "name": "polyp_resection_documented",
            "finding": "colon_polyp",
            "intervention": "polypectomy",
            "operator": "condition",
            "query": {
                "finding": "colon_polyp",
                "intervention": "polypectomy",
                "operator": "condition",
                "condition": {
                    "all": [
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

    assert validator.query.condition is not None
    assert validator.query.condition.all[0].classification == "size_mm"
