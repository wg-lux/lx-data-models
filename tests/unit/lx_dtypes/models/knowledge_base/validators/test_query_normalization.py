"""Shared validator contracts: stable parsing and caller-owned input isolation."""

from copy import deepcopy
from typing import cast

import pytest
from pydantic import ValidationError

from lx_dtypes.models.knowledge_base.validators.ClassificationValidator import (
    ClassificationValidator,
    ClassificationValidatorQuery,
)
from lx_dtypes.models.knowledge_base.validators.FindingsValidator import (
    FindingsValidator,
    FindingsValidatorQuery,
)
from lx_dtypes.models.knowledge_base.validators.InterventionValidator import (
    InterventionValidator,
    InterventionValidatorQuery,
)
from lx_dtypes.models.knowledge_base.validators.UnitValidator import (
    UnitValidator,
    UnitValidatorQuery,
)
from lx_dtypes.models.model import DtypesModel

type Validator = (
    FindingsValidator | ClassificationValidator | InterventionValidator | UnitValidator
)
type Case = tuple[type[Validator], type[DtypesModel], dict[str, str]]


@pytest.fixture(
    params=[
        (FindingsValidator, FindingsValidatorQuery, {}),
        (
            ClassificationValidator,
            ClassificationValidatorQuery,
            {"classification": "size"},
        ),
        (
            InterventionValidator,
            InterventionValidatorQuery,
            {"intervention": "resection"},
        ),
        (UnitValidator, UnitValidatorQuery, {"classification": "size", "unit": "mm"}),
    ]
)
def case(request: pytest.FixtureRequest) -> Case:
    return cast(Case, request.param)


def test_top_level_mapping_and_typed_query_inputs_agree(case: Case) -> None:
    validator_type, query_type, targets = case
    fields = {"finding": "polyp", **targets, "operator": "missing"}
    expected = validator_type.model_validate({"name": "rule", **fields})
    for query in (fields, query_type.model_validate(fields)):
        actual = validator_type.model_validate(
            {
                "name": "rule",
                "uuid": expected.uuid,
                "created_at": expected.created_at,
                "query": query,
            }
        )
        assert actual.model_dump() == expected.model_dump()


def test_mapping_validation_is_repeatable_and_roundtrips(case: Case) -> None:
    validator_type, _, targets = case
    payload = {
        "name": "rule",
        "finding": "polyp",
        **targets,
        "query": {"finding": None},
    }
    original = deepcopy(payload)
    first = validator_type.model_validate(payload)
    assert payload == original
    # Preserve the generated identity when comparing subsequent validations.
    dumped = first.model_dump()
    assert validator_type.model_validate(dumped).model_dump() == dumped
    assert (
        validator_type.model_validate_json(first.model_dump_json()).model_dump()
        == dumped
    )
    assert validator_type.model_validate(first).model_dump() == dumped
    assert validator_type.model_validate(payload).query == first.query
    assert payload == original


def test_typed_query_retains_condition_and_does_not_mutate_input(case: Case) -> None:
    validator_type, query_type, targets = case
    query = query_type.model_validate(
        {
            "operator": "condition",
            "params": {"threshold": 10},
            "condition": {
                "all": [{"classification": "size", "comparator": "in", "value": 10}]
            },
        }
    )
    original = query.model_dump()
    validator = validator_type.model_validate(
        {"name": "rule", "finding": "polyp", **targets, "query": query}
    )
    assert validator.operator == "condition"
    assert validator.query.params == {"threshold": 10}
    assert validator.query.condition is not None
    assert validator.query.condition.all[0].values == [10]
    assert query.model_dump() == original
    validator.query.params["threshold"] = 20
    assert query.model_dump() == original


def test_conflicts_fail_without_mutating_query(case: Case) -> None:
    validator_type, query_type, targets = case
    for field in ("finding", *targets, "operator"):
        query = query_type.model_validate(
            {field: "missing" if field == "operator" else "other"}
        )
        original = query.model_dump()
        with pytest.raises(ValidationError, match=rf"query\.{field} must match"):
            validator_type.model_validate(
                {
                    "name": "rule",
                    "finding": "polyp",
                    **targets,
                    "operator": "exists",
                    "query": query,
                }
            )
        assert query.model_dump() == original


@pytest.mark.parametrize("query", [None, [], "invalid", 42])
def test_malformed_queries_are_rejected(case: Case, query: object) -> None:
    validator_type, _, targets = case
    with pytest.raises(ValidationError):
        validator_type.model_validate(
            {"name": "rule", "finding": "polyp", **targets, "query": query}
        )


def test_strict_query_errors_remain_advisory(case: Case) -> None:
    from lx_dtypes.evaluation import validate_contract

    validator_type, _, targets = case
    payload = {"name": None, "finding": "polyp", **targets, "query": []}
    original = deepcopy(payload)
    result = validate_contract(validator_type, payload)
    assert result.value is None
    assert not result.report.ok
    assert {issue.path for issue in result.report.issues} == {("name",), ("query",)}
    assert payload == original


def test_advisory_batch_reports_errors_after_the_first_invalid_definition() -> None:
    from lx_dtypes.evaluation import validate_contract
    from lx_dtypes.models.model import DtypesRootModel

    result = validate_contract(
        DtypesRootModel[list[FindingsValidator]],
        [
            {"name": "malformed_query", "query": []},
            {"name": "valid_rule", "finding": "polyp"},
            {"name": "another_bad_query", "query": None},
            {"name": "bad_operator", "operator": "invalid"},
        ],
    )
    assert result.value is None
    assert not result.report.ok
    assert {issue.path for issue in result.report.issues} == {
        (0, "query"),
        (2, "query"),
        (3, "operator"),
        (3, "query", "operator"),
    }
