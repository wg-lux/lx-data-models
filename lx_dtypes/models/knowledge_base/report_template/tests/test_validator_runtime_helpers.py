from __future__ import annotations

from typing import cast

from lx_dtypes.models.knowledge_base.classification.Classification import (
    Classification,
)
from lx_dtypes.models.knowledge_base.classification_choice.ClassificationChoice import (
    ClassificationChoice,
)
from lx_dtypes.models.knowledge_base.classification_choice_descriptor.ClassificationChoiceDescriptor import (
    ClassificationChoiceDescriptor,
)
from lx_dtypes.models.knowledge_base.intervention.Intervention import Intervention
from lx_dtypes.models.knowledge_base.report_template.ClassificationValidator import (
    ClassificationValidator,
)
from lx_dtypes.models.knowledge_base.report_template.FindingsValidator import (
    FindingsValidatorConditionClause,
    FindingsValidator,
)
from lx_dtypes.models.knowledge_base.report_template.InterventionValidator import (
    InterventionValidator,
)
from lx_dtypes.models.knowledge_base.report_template.UnitValidator import UnitValidator
from lx_dtypes.models.knowledge_base.report_template.ValidatorRequirementReference import (
    ValidatorRequirementReference,
)
from lx_dtypes.models.knowledge_base.report_template import ValidatorRuntime as runtime
from lx_dtypes.models.knowledge_base.report_template.ValueTypes import ValidationScalar
from lx_dtypes.models.knowledge_base.unit.Unit import Unit


def _normalize_clause_or_fail(
    clause: FindingsValidatorConditionClause,
) -> runtime._NormalizedConditionClause:
    normalized = runtime._normalize_condition_clause(clause)
    assert (
        normalized is not None
    ), "test clause should always normalize to a condition clause"
    return normalized


def test_runtime_normalizers_cover_mapping_and_sequence_shapes() -> None:
    classifications, units = runtime._normalize_classifications(
        [
            {
                "classification": "size_mm",
                "value": "12",
                "unit": "mm",
            },
            {
                "name": "morphology",
                "values": ["sessile", "flat"],
            },
            "bleeding",
        ]
    )

    interventions = runtime._normalize_interventions(
        [{"intervention": "resection"}, {"name": "biopsy"}, "argon"]
    )
    findings = runtime._normalize_reported_findings(
        [
            {
                "name": "colon_polyp",
                "classifications": [
                    {"classification": "size_mm", "value": 12, "unit": "mm"}
                ],
                "interventions": [{"intervention": "resection"}],
            },
            {"finding": None},
        ]
    )

    assert classifications["size_mm"] == ["12"]
    assert classifications["morphology"] == ["sessile", "flat"]
    assert classifications["bleeding"] == [True]
    assert units["size_mm"] == ["mm"]
    assert interventions == ["resection", "biopsy", "argon"]
    assert len(findings) == 1
    assert findings[0]["finding"] == "colon_polyp"
    assert findings[0]["classification_units"]["size_mm"] == ["mm"]


def test_runtime_clause_evaluation_covers_all_comparators() -> None:
    values: dict[str, list[ValidationScalar]] = {
        "size_mm": [12, "15"],
        "morphology": ["sessile"],
        "location": ["left_colon"],
    }

    assert runtime._evaluate_clause(
        _normalize_clause_or_fail(
            FindingsValidatorConditionClause(
                classification="morphology",
                comparator="eq",
                value="sessile",
            )
        ),
        values,
    )
    assert not runtime._evaluate_clause(
        _normalize_clause_or_fail(
            FindingsValidatorConditionClause(
                classification="morphology",
                comparator="eq",
                value="pedunculated",
            )
        ),
        values,
    )
    assert runtime._evaluate_clause(
        _normalize_clause_or_fail(
            FindingsValidatorConditionClause(
                classification="morphology",
                comparator="ne",
                value="pedunculated",
            )
        ),
        values,
    )
    assert not runtime._evaluate_clause(
        _normalize_clause_or_fail(
            FindingsValidatorConditionClause(
                classification="morphology",
                comparator="ne",
                value="sessile",
            )
        ),
        values,
    )
    assert runtime._evaluate_clause(
        _normalize_clause_or_fail(
            FindingsValidatorConditionClause(
                classification="size_mm",
                comparator="gt",
                value=10,
            )
        ),
        values,
    )
    assert runtime._evaluate_clause(
        _normalize_clause_or_fail(
            FindingsValidatorConditionClause(
                classification="size_mm",
                comparator="gt",
                value=12,
            )
        ),
        values,
    )
    assert runtime._evaluate_clause(
        _normalize_clause_or_fail(
            FindingsValidatorConditionClause(
                classification="size_mm",
                comparator="gte",
                value=12,
            )
        ),
        values,
    )
    assert runtime._evaluate_clause(
        _normalize_clause_or_fail(
            FindingsValidatorConditionClause(
                classification="size_mm",
                comparator="gte",
                value=13,
            )
        ),
        values,
    )
    assert runtime._evaluate_clause(
        _normalize_clause_or_fail(
            FindingsValidatorConditionClause(
                classification="size_mm",
                comparator="lt",
                value=20,
            )
        ),
        values,
    )
    assert not runtime._evaluate_clause(
        _normalize_clause_or_fail(
            FindingsValidatorConditionClause(
                classification="size_mm",
                comparator="lt",
                value=12,
            )
        ),
        values,
    )
    assert runtime._evaluate_clause(
        _normalize_clause_or_fail(
            FindingsValidatorConditionClause(
                classification="size_mm",
                comparator="lte",
                value=12,
            )
        ),
        values,
    )
    assert not runtime._evaluate_clause(
        _normalize_clause_or_fail(
            FindingsValidatorConditionClause(
                classification="size_mm",
                comparator="lte",
                value=11,
            )
        ),
        values,
    )
    assert runtime._evaluate_clause(
        _normalize_clause_or_fail(
            FindingsValidatorConditionClause(
                classification="location",
                comparator="in",
                values=["left_colon", "rectum"],
            )
        ),
        values,
    )
    assert not runtime._evaluate_clause(
        _normalize_clause_or_fail(
            FindingsValidatorConditionClause(
                classification="location",
                comparator="in",
                values=["transverse"],
            )
        ),
        values,
    )
    assert runtime._evaluate_clause(
        _normalize_clause_or_fail(
            FindingsValidatorConditionClause(
                classification="location",
                comparator="not_in",
                values=["right_colon"],
            )
        ),
        values,
    )
    assert not runtime._evaluate_clause(
        _normalize_clause_or_fail(
            FindingsValidatorConditionClause(
                classification="location",
                comparator="not_in",
                values=["left_colon"],
            )
        ),
        values,
    )
    assert not runtime._evaluate_clause(
        _normalize_clause_or_fail(
            FindingsValidatorConditionClause(
                classification="missing",
                comparator="eq",
                value="x",
            )
        ),
        values,
    )


def test_normalize_condition_clause_returns_none_for_blank_classification() -> None:
    clause = FindingsValidatorConditionClause(
        classification="",
        comparator="eq",
        value="x",
    )
    assert runtime._normalize_condition_clause(clause) is None


def test_missing_requirement_references_cover_all_reference_kinds() -> None:
    occurrence = runtime._RuntimeFindingOccurrence(
        finding="colon_polyp",
        classifications={"size_mm": [12]},
        classification_units={"size_mm": ["mm"]},
        interventions=["resection"],
    )

    requirements = [
        ValidatorRequirementReference(kind="classification", name="morphology"),
        ValidatorRequirementReference(kind="finding", name="ulcer"),
        ValidatorRequirementReference(kind="intervention", name="biopsy"),
        ValidatorRequirementReference(
            kind="unit",
            name="cm",
            classification="size_mm",
        ),
    ]

    assert runtime._missing_requirement_references(
        requirements,
        occurrence=occurrence,
        all_occurrences=[occurrence],
    ) == [
        "classification:morphology",
        "finding:ulcer",
        "intervention:biopsy",
        "unit:cm",
    ]


def test_classification_data_type_hint_covers_binary_and_non_categorical() -> None:
    boolean_descriptor = ClassificationChoiceDescriptor.model_validate(
        {
            "name": "present_descriptor",
            "classification_choice_descriptor_type": "boolean",
            "selection_multiple": False,
        }
    )
    numeric_descriptor = ClassificationChoiceDescriptor.model_validate(
        {
            "name": "size_descriptor",
            "classification_choice_descriptor_type": "numeric",
            "selection_multiple": False,
        }
    )
    binary_choice = ClassificationChoice.model_validate(
        {
            "name": "present_choice",
            "classification_choice_descriptors": ["present_descriptor"],
        }
    )
    numeric_choice = ClassificationChoice.model_validate(
        {
            "name": "size_choice",
            "classification_choice_descriptors": ["size_descriptor"],
        }
    )

    binary_classification = Classification.model_validate(
        {
            "name": "binary_classification",
            "classification_choices": ["present_choice", "absent_choice"],
        }
    )
    numeric_classification = Classification.model_validate(
        {
            "name": "numeric_classification",
            "classification_choices": ["size_choice"],
        }
    )

    assert (
        runtime._classification_data_type_hint(
            classification=binary_classification,
            classification_choices={"present_choice": binary_choice},
            classification_choice_descriptors={
                "present_descriptor": boolean_descriptor
            },
        )[0]
        == "binary"
    )
    assert (
        runtime._classification_data_type_hint(
            classification=numeric_classification,
            classification_choices={"size_choice": numeric_choice},
            classification_choice_descriptors={"size_descriptor": numeric_descriptor},
        )[0]
        == "non_categorical"
    )
    assert (
        runtime._classification_data_type_hint(
            classification=None,
            classification_choices={},
            classification_choice_descriptors={},
        )[0]
        == "unknown"
    )


def test_findings_runtime_reports_missing_generic_references() -> None:
    validator = FindingsValidator.model_validate(
        {
            "name": "polyp_requires_context",
            "finding": "colon_polyp",
            "operator": "condition",
            "query": {
                "finding": "colon_polyp",
                "operator": "condition",
                "condition": {
                    "all": [
                        {
                            "classification": "size_mm",
                            "comparator": "gte",
                            "value": 10,
                        }
                    ],
                    "then_requires": [
                        {"kind": "finding", "name": "bleeding"},
                        {"kind": "intervention", "name": "resection"},
                        {
                            "kind": "unit",
                            "name": "cm",
                            "classification": "size_mm",
                        },
                    ],
                },
            },
        }
    )

    result = runtime.evaluate_findings_validator_runtime(
        validator,
        reported_findings=[
            {
                "finding": "colon_polyp",
                "classifications": [{"classification": "size_mm", "value": 12}],
            }
        ],
    )

    assert result["ok"] is False
    assert result["triggered_occurrences"] == 1
    assert result["issues"][0]["code"] == "missing_required_reference"
    assert result["issues"][0]["details"]["missing_requirements"] == [
        "finding:bleeding",
        "intervention:resection",
        "unit:cm",
    ]


def test_intervention_validator_runtime_covers_condition_missing_and_unsupported() -> (
    None
):
    validator = InterventionValidator.model_validate(
        {
            "name": "needs_resection_if_large",
            "finding": "colon_polyp",
            "intervention": "resection",
            "operator": "condition",
            "query": {
                "finding": "colon_polyp",
                "intervention": "resection",
                "operator": "condition",
                "condition": {
                    "all": [
                        {
                            "classification": "size_mm",
                            "comparator": "gt",
                            "value": 10,
                        }
                    ],
                    "then_requires": [{"kind": "finding", "name": "bleeding"}],
                },
            },
        }
    )

    missing_result = runtime.evaluate_intervention_validator_runtime(
        validator,
        interventions={"resection": Intervention(name="resection")},
        reported_findings=[
            {
                "finding": "colon_polyp",
                "classifications": [{"classification": "size_mm", "value": 12}],
                "interventions": [],
            }
        ],
    )
    unsupported_result = runtime.evaluate_intervention_validator_runtime(
        cast(
            InterventionValidator,
            type(
                "_UnsupportedInterventionValidator",
                (),
                {
                    "name": "bad_intervention",
                    "finding": "colon_polyp",
                    "intervention": "resection",
                    "operator": "invalid",
                    "precedence": "required",
                    "query": type(
                        "_UnsupportedInterventionQuery", (), {"condition": None}
                    )(),
                },
            )(),
        ),
        interventions={},
        reported_findings=[],
    )

    assert missing_result["ok"] is False
    assert missing_result["issues"][0]["code"] == "missing_required_intervention"
    assert missing_result["issues"][0]["details"]["missing_requirements"] == [
        "finding:bleeding"
    ]
    assert unsupported_result["issues"][0]["code"] == (
        "unsupported_intervention_validator_operator"
    )


def test_unit_validator_runtime_covers_exists_missing_condition_and_unsupported() -> (
    None
):
    exists_validator = UnitValidator.model_validate(
        {
            "name": "needs_mm",
            "finding": "colon_polyp",
            "classification": "size_mm",
            "unit": "mm",
            "operator": "exists",
        }
    )
    missing_validator = UnitValidator.model_validate(
        {
            "name": "forbid_cm",
            "finding": "colon_polyp",
            "classification": "size_mm",
            "unit": "cm",
            "operator": "missing",
        }
    )
    condition_validator = UnitValidator.model_validate(
        {
            "name": "needs_mm_if_large",
            "finding": "colon_polyp",
            "classification": "size_mm",
            "unit": "mm",
            "operator": "condition",
            "query": {
                "finding": "colon_polyp",
                "classification": "size_mm",
                "unit": "mm",
                "operator": "condition",
                "condition": {
                    "all": [
                        {
                            "classification": "size_mm",
                            "comparator": "gte",
                            "value": 10,
                        }
                    ],
                    "then_requires": [{"kind": "intervention", "name": "resection"}],
                },
            },
        }
    )

    payload = [
        {
            "finding": "colon_polyp",
            "classifications": [
                {"classification": "size_mm", "value": 12, "unit": "mm"}
            ],
            "interventions": [],
        }
    ]

    assert runtime.evaluate_unit_validator_runtime(
        exists_validator,
        units={"mm": Unit(name="mm", abbreviation="mm")},
        reported_findings=payload,
    )["ok"]
    assert runtime.evaluate_unit_validator_runtime(
        missing_validator,
        units={},
        reported_findings=payload,
    )["ok"]

    missing_condition = runtime.evaluate_unit_validator_runtime(
        condition_validator,
        units={"mm": Unit(name="mm", abbreviation="mm")},
        reported_findings=payload,
    )
    unsupported = runtime.evaluate_unit_validator_runtime(
        cast(
            UnitValidator,
            type(
                "_UnsupportedUnitValidator",
                (),
                {
                    "name": "bad_unit",
                    "finding": "colon_polyp",
                    "classification": "size_mm",
                    "unit": "mm",
                    "operator": "invalid",
                    "precedence": "required",
                    "query": type("_UnsupportedUnitQuery", (), {"condition": None})(),
                },
            )(),
        ),
        units={},
        reported_findings=[],
    )

    assert missing_condition["ok"] is False
    assert missing_condition["issues"][0]["code"] == "missing_required_unit"
    assert missing_condition["issues"][0]["details"]["missing_requirements"] == [
        "intervention:resection"
    ]
    assert unsupported["issues"][0]["code"] == "unsupported_unit_validator_operator"


def test_classification_validator_runtime_covers_missing_condition_and_unsupported() -> (
    None
):
    validator = ClassificationValidator.model_validate(
        {
            "name": "needs_lst_if_large",
            "finding": "colon_polyp",
            "classification": "lst",
            "operator": "condition",
            "query": {
                "finding": "colon_polyp",
                "classification": "lst",
                "operator": "condition",
                "condition": {
                    "all": [
                        {
                            "classification": "size_mm",
                            "comparator": "gt",
                            "value": 10,
                        }
                    ],
                    "then_requires": [{"kind": "intervention", "name": "resection"}],
                },
            },
        }
    )

    choice = ClassificationChoice.model_validate(
        {
            "name": "size_choice",
            "classification_choice_descriptors": ["size_descriptor"],
        }
    )
    descriptor = ClassificationChoiceDescriptor.model_validate(
        {
            "name": "size_descriptor",
            "classification_choice_descriptor_type": "numeric",
            "selection_multiple": False,
        }
    )
    classification = Classification.model_validate(
        {
            "name": "lst",
            "classification_choices": ["size_choice"],
        }
    )

    result = runtime.evaluate_classification_validator_runtime(
        validator,
        classifications={"lst": classification},
        classification_choices={"size_choice": choice},
        classification_choice_descriptors={"size_descriptor": descriptor},
        reported_findings=[
            {
                "finding": "colon_polyp",
                "classifications": [{"classification": "size_mm", "value": 12}],
                "interventions": [],
            }
        ],
    )
    unsupported = runtime.evaluate_classification_validator_runtime(
        cast(
            ClassificationValidator,
            type(
                "_UnsupportedClassificationValidator",
                (),
                {
                    "name": "bad_classification",
                    "finding": "colon_polyp",
                    "classification": "lst",
                    "operator": "invalid",
                    "precedence": "required",
                    "query": type(
                        "_UnsupportedClassificationQuery",
                        (),
                        {"condition": None},
                    )(),
                },
            )(),
        ),
        classifications={},
        classification_choices={},
        classification_choice_descriptors={},
        reported_findings=[],
    )

    assert result["ok"] is False
    assert result["issues"][0]["code"] == "missing_required_reference"
    assert result["issues"][0]["details"]["missing_requirements"] == [
        "intervention:resection"
    ]
    assert unsupported["issues"][0]["code"] == (
        "unsupported_classification_validator_operator"
    )
