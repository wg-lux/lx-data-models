from importlib.resources import files

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.cohort_definition import CohortDefinition, CohortFilters
from lx_dtypes.models.contracts.study_setup import StudySetupDefinition
from lx_dtypes.utils.study_setup_yaml import parse_study_setup_yaml


def template() -> str:
    return files("lx_dtypes").joinpath("data/study_setup/research.yml").read_text()


def test_template_preserves_live_definition_semantics_and_shared_contracts() -> None:
    setup = parse_study_setup_yaml(template())
    assert [item.dataset_type for item in setup.datasets] == ["image", "video"]
    assert setup.cohorts[0].filters.has_report is False
    assert setup.cohorts[0].filters.date_from == "2026-01-01"
    assert setup.cohorts[0].dataset_refs == ["colorectal_images", "colorectal_videos"]
    assert setup.cohorts[1].dataset_refs == ["colorectal_images"]
    assert setup.cohorts[2].dataset_refs == []
    assert isinstance(setup.cohorts[0].filters, CohortFilters)
    assert CohortDefinition.model_fields["filters"].annotation is CohortFilters
    assert StudySetupDefinition.model_validate_json(setup.model_dump_json()) == setup
    schema = StudySetupDefinition.model_json_schema()
    assert schema["additionalProperties"] is False
    assert "CohortFilters" in schema["$defs"]


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("schema_version: '1.0'", "schema_version: '2.0'"),
        ("has_report: false", "has_report: 'false'"),
        ("is_active: true", "is_active: 'true'"),
        ("date_to: '2026-12-31'", "date_to: '2025-12-31'"),
        ("date_from: '2026-01-01'", "date_from: '2026-02-30'"),
        ("date_from: '2026-01-01'", "date_from: 2026-01-01"),
        ("dataset_type: image", "dataset_type: text"),
        (
            "ai_model_type: image_multilabel_classification",
            "ai_model_type: video_segment_classification",
        ),
        (
            "hypothesis: Linked image and video annotations support joint examination review.",
            "hypothesis: ' '",
        ),
        (
            "hypothesis: Linked image and video annotations support joint examination review.",
            "",
        ),
        ("definition_id: image_review", "definition_id: colorectal_images"),
        ("dataset_refs: [colorectal_images]", "dataset_refs: [missing_dataset]"),
        (
            "dataset_refs: [colorectal_images]",
            "dataset_refs: [colorectal_images, colorectal_images]",
        ),
        ("limit: 100", "limit: 501"),
        ("limit: 100", "limit: true"),
        ("has_report: false", "hasReport: false"),
        ("definition_version: '1.0.0'", "definition_version: 1"),
    ],
)
def test_invalid_definition_is_rejected(old: str, new: str) -> None:
    with pytest.raises(ValidationError):
        parse_study_setup_yaml(template().replace(old, new))


@pytest.mark.parametrize(
    "field", ["owner", "permissions", "patient_records", "host_path"]
)
def test_host_owned_fields_are_rejected(field: str) -> None:
    with pytest.raises(ValidationError):
        parse_study_setup_yaml(template() + f"\n{field}: forbidden\n")


@pytest.mark.parametrize(
    "raw",
    [
        "name: one\nname: two",
        "filters: {has_report: true, has_report: false}",
        "name: &name value\ncopy: *name",
        "name: &name [*name]",
        "!!python/object:builtins.object {}",
        "<<: {name: merged}",
        "1: value",
        "---\n{}\n---\n{}",
        "[" * 33 + "]" * 33,
        "#" * 1_048_577,
        "#" + "ü" * 524_288,
        "[" + "0," * 50_001 + "]",
        "",
    ],
)
def test_unsafe_or_unbounded_yaml_is_rejected(raw: str) -> None:
    with pytest.raises(ValueError):
        parse_study_setup_yaml(raw)


@pytest.mark.parametrize("has_report", [True, False, None])
def test_http_and_yaml_share_filter_validation(has_report: bool | None) -> None:
    cohort = CohortDefinition.model_validate(
        {"name": "Study", "hypothesis": "Review", "filters": {"has_report": has_report}}
    )
    assert cohort.filters.has_report is has_report
    with pytest.raises(ValidationError):
        CohortDefinition.model_validate(
            {"name": "Study", "hypothesis": "Review", "dataset_ids": [1, 1]}
        )
