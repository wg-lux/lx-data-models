from copy import deepcopy

import pytest
from pydantic import BaseModel, ConfigDict, field_validator

from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.validation import assess_examination, validate_contract
from tests.paths import PACKAGE_ROOT


class ExampleContract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    count: int

    @field_validator("count")
    @classmethod
    def positive(cls, value: int) -> int:
        if value < 0:
            raise ValueError(f"Sensitive submitted value: {value}")
        return value


@pytest.fixture(scope="module")
def kb() -> KnowledgeBase:
    loader = DataLoader(input_dirs=[PACKAGE_ROOT / "data"])
    loader.load_module_configs()
    return loader.load_knowledge_base("report_template_examples")


def examination(kb: KnowledgeBase) -> dict[str, object]:
    return {
        "patient": "synthetic_patient",
        "examination": "star_upper_gi_endoscopy",
        **kb.config.knowledge_base_identity.model_dump(),
    }


def test_contract_collects_errors_and_preserves_input() -> None:
    payload = {"unexpected": "private value"}
    result = validate_contract(ExampleContract, payload)
    assert result.value is None
    assert not result.report.ok
    assert [(issue.code, issue.path) for issue in result.report.issues] == [
        ("contract.missing", ("count",)),
        ("contract.extra_forbidden", ("unexpected",)),
    ]
    assert "private value" not in result.model_dump_json()
    assert payload == {"unexpected": "private value"}


def test_contract_does_not_leak_custom_error_context() -> None:
    result = validate_contract(ExampleContract, {"count": -123456})
    assert result.report.issues[0].code == "contract.value_error"
    assert "123456" not in result.model_dump_json()


def test_contract_revalidates_mutated_instances() -> None:
    value = ExampleContract(count=2)
    value.count = -1
    assert validate_contract(ExampleContract, value).value is None
    assert validate_contract(ExampleContract, {"count": 2}).value == ExampleContract(
        count=2
    )
    assert not validate_contract(ExampleContract, {"count": "2"}).report.ok


def test_programming_errors_are_not_hidden() -> None:
    class BrokenContract(BaseModel):
        count: int

        @field_validator("count")
        @classmethod
        def broken(cls, value: int) -> int:
            raise RuntimeError("broken validator")

    with pytest.raises(RuntimeError, match="broken validator"):
        validate_contract(BrokenContract, {"count": 1})


def test_assessment_reuses_study_engine_without_mutation(kb: KnowledgeBase) -> None:
    from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination

    payload = examination(kb)
    original = deepcopy(payload)
    result = assess_examination(kb, payload, template_name="star_upper_gi_main")
    runtime = kb.evaluate_report_template_validators(
        "star_upper_gi_main", p_examination=PExamination.model_validate(payload)
    )
    assert result.study_evaluated
    assert result.ok == runtime["ok"]
    assert [issue.code for issue in result.issues] == [
        item["code"] for item in runtime["issues"]
    ]
    assert payload == original
    assert result.knowledge_base_identity == kb.config.knowledge_base_identity
    assert '"schema_version":"1.0"' in result.model_dump_json()


@pytest.mark.parametrize("partial", [False, True])
def test_identity_mismatch_skips_study(kb: KnowledgeBase, partial: bool) -> None:
    payload = examination(kb)
    payload["knowledge_base_version"] = "wrong-version"
    if partial:
        payload.pop("knowledge_base_module")
    result = assess_examination(kb, payload, template_name="star_upper_gi_main")
    assert not result.ok
    assert not result.study_evaluated
    assert result.issues[0].code == "terminology.identity_mismatch"


def test_legacy_identity_is_advisory(kb: KnowledgeBase) -> None:
    payload = examination(kb)
    payload.pop("knowledge_base_module")
    payload.pop("knowledge_base_version")
    result = assess_examination(kb, payload)
    assert result.ok
    assert result.issues[0].level == "warning"
    assert result.issues[0].code == "terminology.identity_missing"
    assert not result.study_evaluated


def test_unknown_template_is_reported(kb: KnowledgeBase) -> None:
    result = assess_examination(kb, examination(kb), template_name="unknown")
    assert result.issues[0].code == "terminology.template_unknown"
    assert not result.ok
    assert not result.study_evaluated


def test_semantic_failure_is_non_blocking(kb: KnowledgeBase) -> None:
    payload = examination(kb)
    payload["examination"] = "unknown"
    result = assess_examination(kb, payload)
    assert not result.ok
    assert result.issues[0].code == "terminology.inadmissible"
    assert not result.study_evaluated


def test_schema_failure_is_non_blocking(kb: KnowledgeBase) -> None:
    result = assess_examination(kb, {})
    assert not result.ok
    assert all(issue.source == "contract" for issue in result.issues)
    assert not result.study_evaluated
