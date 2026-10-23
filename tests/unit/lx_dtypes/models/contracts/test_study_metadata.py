import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.study_metadata import StudyMetadata
from lx_dtypes.models.interface.data_roots import package_data_root
from lx_dtypes.models.knowledge_base.study_preset import StudyPreset
from lx_dtypes.utils.study_setup_yaml import parse_study_setup_yaml


def metadata_payload():
    return {
        "participating_centers": [{"center_key": "center_a", "name": "Center A"}],
        "age_groups": [{"name": "Adults", "minimum_age": 18, "maximum_age": 65}],
        "terminology_requirements": [
            {"module": "coloreg", "version": "0.1.0"},
            {"module": "coloreg", "version": "0.2.0"},
        ],
        "inclusion_criteria": [
            {
                "name": "Polyp",
                "concepts": [
                    {
                        "module": "coloreg",
                        "version": version,
                        "kind": "finding",
                        "name": "polyp",
                    }
                    for version in ("0.1.0", "0.2.0")
                ],
            }
        ],
    }


def test_metadata_and_preset_round_trip_preserve_exact_versions():
    metadata = StudyMetadata.model_validate(metadata_payload())
    preset = StudyPreset(name="research", study_metadata=metadata)
    assert StudyPreset.model_validate(preset.ddict).study_metadata == metadata
    assert StudyMetadata.model_validate_json(metadata.model_dump_json()) == metadata


@pytest.mark.parametrize(
    "field,value",
    [
        ("age_groups", [{"name": "invalid", "minimum_age": 60, "maximum_age": 18}]),
        ("age_groups", [{"name": "invalid", "minimum_age": True}]),
        ("age_groups", [{"name": "invalid", "minimum_age": -1}]),
        ("terminology_requirements", []),
        ("terminology_requirements", [{"module": "coloreg", "version": "*"}]),
        ("inclusion_criteria", [{"name": "empty", "concepts": []}]),
        ("participating_centers", [{"center_key": " ", "name": "Invalid"}]),
    ],
)
def test_invalid_metadata_rejected(field, value):
    payload = metadata_payload()
    payload[field] = value
    with pytest.raises(ValidationError):
        StudyMetadata.model_validate(payload)


@pytest.mark.parametrize(
    "field",
    [
        "participating_centers",
        "age_groups",
        "terminology_requirements",
        "inclusion_criteria",
    ],
)
def test_duplicate_metadata_identities_rejected(field):
    payload = metadata_payload()
    payload[field].append(payload[field][0])
    with pytest.raises(ValidationError, match="unique"):
        StudyMetadata.model_validate(payload)


def test_analysis_metadata_preserves_rules_and_requires_exact_dependency():
    setup = parse_study_setup_yaml(
        (package_data_root() / "study_metadata/coloreg_resection.yml").read_text()
    )
    metadata = setup.cohorts[1].study_metadata
    assert metadata.analysis_definitions[0].status == "ready"
    preset = StudyPreset(name="analysis", study_metadata=metadata)
    assert StudyPreset.model_validate(preset.ddict).study_metadata == metadata
    payload = metadata.model_dump(mode="python")
    payload["terminology_requirements"] = []
    with pytest.raises(ValidationError, match="analysis definitions require"):
        StudyMetadata.model_validate(payload)


def test_analysis_names_are_unique_and_unresolved_protocols_remain_drafts():
    setup = parse_study_setup_yaml(
        (package_data_root() / "study_metadata/coloreg_resection.yml").read_text()
    )
    for index in (0, 2, 3):
        analysis = setup.cohorts[index].study_metadata.analysis_definitions[0]
        payload = analysis.model_dump(mode="python")
        payload["status"] = "ready"
        with pytest.raises(ValidationError, match="unresolved"):
            type(analysis).model_validate(payload)
    metadata = setup.cohorts[1].study_metadata.model_dump(mode="python")
    metadata["analysis_definitions"] *= 2
    with pytest.raises(ValidationError, match="unique"):
        StudyMetadata.model_validate(metadata)
