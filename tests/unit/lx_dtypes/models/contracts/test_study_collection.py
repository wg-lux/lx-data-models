from datetime import UTC, datetime
from math import isnan
from uuid import UUID

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts import StudyCollectionRecord
from lx_dtypes.models.contracts.dtypes_record_persistence import (
    DtypesRecordPersistencePayload,
)
from lx_dtypes.models.contracts.knowledge_base import KnowledgeBaseIdentity
from lx_dtypes.models.contracts.study import StudyDefinition
from lx_dtypes.models.contracts.validation import ValidationIssue, ValidationReport


def collection() -> StudyCollectionRecord:
    identity = KnowledgeBaseIdentity(
        knowledge_base_module="synthetic", knowledge_base_version="1.0.0"
    )
    return StudyCollectionRecord(
        record_uuid=UUID(int=1),
        study_uuid=UUID(int=2),
        study_definition=StudyDefinition(name="Synthetic study"),
        patient_examination_uuid=UUID(int=3),
        package_snapshot_id="sha256:" + "a" * 64,
        record=DtypesRecordPersistencePayload(
            uuid=UUID(int=4),
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            patient="synthetic-patient",
            examination="synthetic-examination",
            knowledge_base_module=identity.knowledge_base_module,
            knowledge_base_version=identity.knowledge_base_version,
        ),
        evaluation=ValidationReport(knowledge_base_identity=identity),
        evaluated_at=datetime(2026, 1, 1, tzinfo=UTC),
        language="en",
    )


def test_json_roundtrip_preserves_raw_ledger_and_independent_host_identity() -> None:
    record = collection()
    restored = StudyCollectionRecord.model_validate_json(record.model_dump_json())
    assert restored.model_dump(mode="json") == record.model_dump(mode="json")
    assert restored.record.uuid != restored.patient_examination_uuid


@pytest.mark.parametrize("field", ["knowledge_base_module", "knowledge_base_version"])
@pytest.mark.parametrize("value", [None, "other"])
def test_rejects_incomplete_or_conflicting_identity(
    field: str, value: str | None
) -> None:
    record = collection().model_dump()
    record["record"][field] = value
    with pytest.raises(ValidationError):
        StudyCollectionRecord.model_validate(record)


@pytest.mark.parametrize("source", ["contract", "terminology"])
def test_rejects_non_study_validation_errors(source: str) -> None:
    record = collection().model_dump(round_trip=True)
    record["evaluation"]["issues"] = (
        {"code": "invalid", "message": "invalid", "source": source, "level": "error"},
    )
    with pytest.raises(ValidationError, match="prevent collection"):
        StudyCollectionRecord.model_validate(record)


def test_failed_study_evaluation_is_valid_collection_data() -> None:
    record = collection().model_dump(round_trip=True)
    record["report_template_name"] = "synthetic-template"
    record["evaluation"]["study_evaluated"] = True
    record["evaluation"]["issues"] = (
        ValidationIssue(code="required", message="missing", source="study"),
    )
    result = StudyCollectionRecord.model_validate(record)
    assert not result.evaluation.ok
    assert StudyCollectionRecord.model_validate_json(
        result.model_dump_json()
    ).model_dump(mode="json") == result.model_dump(mode="json")


def test_study_issues_cannot_claim_unevaluated_template() -> None:
    record = collection().model_dump(round_trip=True)
    record["evaluation"]["issues"] = (
        ValidationIssue(code="required", message="missing", source="study"),
    )
    with pytest.raises(ValidationError, match="completed study evaluation"):
        StudyCollectionRecord.model_validate(record)


@pytest.mark.parametrize(
    "update",
    [
        {"report_template_name": "template"},
        {"report_template_name": " "},
        {"evaluated_at": datetime(2026, 1, 1)},  # noqa: DTZ001 - Test rejection of naive timestamps.
        {"language": "fr"},
        {"unknown": "value"},
        {"package_snapshot_id": "sha256:invalid"},
        {"package_snapshot_id": "a" * 64},
        {"cohort_uuid": UUID(int=5)},
        {"cohort_definition": {"name": "cohort", "hypothesis": "synthetic"}},
        {"study_definition": {"name": " "}},
    ],
)
def test_rejects_invalid_provenance(update: dict[str, object]) -> None:
    data = collection().model_dump(round_trip=True)
    data.update(update)
    with pytest.raises(ValidationError):
        StudyCollectionRecord.model_validate(data)


def test_rejects_forged_computed_result_and_mutated_ledger() -> None:
    record = collection()
    data = record.model_dump()
    data["evaluation"]["ok"] = False
    with pytest.raises(ValidationError, match="conflicts"):
        StudyCollectionRecord.model_validate(data)
    record.record.knowledge_base_version = "different"
    with pytest.raises(ValidationError):
        StudyCollectionRecord.model_validate(
            {**record.model_dump(round_trip=True), "record": record.record}
        )


@pytest.mark.parametrize("value", [True, 3, 2.5, "raw", ["a", "b"], float("nan"), {}])
def test_descriptor_values_are_validated_without_substitution(value: object) -> None:
    data = collection().model_dump(round_trip=True)
    data["record"]["patient_indications"] = [
        {
            "indication": "screening",
            "patient_examination": "synthetic-examination",
            "patient_indication_classifications": [
                {
                    "classification": "screening",
                    "classification_choice": "eligible",
                    "patient_indication": "screening",
                    "patient_indication_classification_descriptors": [
                        {
                            "descriptor_value": value,
                            "classification_choice_descriptor": "raw",
                            "patient_indication_classification": "screening",
                        }
                    ],
                }
            ],
        }
    ]
    if isinstance(value, dict) or (isinstance(value, float) and isnan(value)):
        with pytest.raises(ValidationError):
            StudyCollectionRecord.model_validate(data)
    else:
        result = StudyCollectionRecord.model_validate(data)
        restored = StudyCollectionRecord.model_validate_json(result.model_dump_json())
        descriptor = (
            restored.record.patient_indications[0]
            .patient_indication_classifications[0]
            .patient_indication_classification_descriptors[0]
        )
        assert descriptor.descriptor_value == value
        assert type(descriptor.descriptor_value) is type(value)
