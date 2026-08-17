from __future__ import annotations

from types import SimpleNamespace
from typing import Any, NoReturn

import pytest

from lx_dtypes.django.api import findings_routes, indications_routes


class _ApiError(RuntimeError):
    def __init__(self, status: int, code: str, message: str) -> None:
        self.status = status
        self.code = code
        super().__init__(message)


class _Relation(list[Any]):
    def all(self) -> "_Relation":
        return self

    def prefetch_related(self, *args: str) -> "_Relation":
        del args
        return self


def _api_error(status: int, code: str, message: str) -> NoReturn:
    raise _ApiError(status, code, message)


def _orm_models_for_patient_examination(patient_examination: object) -> Any:
    class _Query:
        def filter(self, **kwargs: object) -> "_Query":
            del kwargs
            return self

        def first(self) -> object:
            return patient_examination

    return lambda: {"PatientExamination": SimpleNamespace(objects=_Query())}


def _lookup(
    *,
    examinations: dict[str, dict[str, Any]] | None = None,
    findings: dict[str, dict[str, Any]] | None = None,
    classifications: dict[str, dict[str, Any]] | None = None,
) -> dict[str, dict[str, dict[str, Any]]]:
    return {
        "examination": examinations or {},
        "finding": findings or {},
        "classification": classifications or {},
        "classification_choice": {},
        "indication": {},
    }


@pytest.mark.parametrize(
    "resolver, record",
    [
        (
            findings_routes._resolve_exam_kb_finding_names,
            SimpleNamespace(name="colonoscopy"),
        ),
        (
            findings_routes._resolve_kb_finding_classification_names,
            SimpleNamespace(name="colon_polyp"),
        ),
        (
            findings_routes._resolve_kb_classification_choice_names,
            SimpleNamespace(name="polyp_size"),
        ),
        (
            indications_routes._resolve_kb_finding_names,
            SimpleNamespace(name="colonoscopy"),
        ),
        (
            indications_routes._resolve_exam_kb_indication_names,
            SimpleNamespace(name="colonoscopy"),
        ),
    ],
)
def test_resolution_helpers_fail_closed_when_concept_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    resolver: Any,
    record: SimpleNamespace,
) -> None:
    monkeypatch.setattr(
        findings_routes, "_kb_lookup", lambda *args, **kwargs: _lookup()
    )

    assert resolver(record, module_name="incompatible_module", version="1.0.0") == set()


@pytest.mark.parametrize(
    "resolver, record_name, lookup",
    [
        (
            findings_routes._resolve_exam_kb_finding_names,
            "colonoscopy",
            _lookup(examinations={"colonoscopy": {"findings": "colon_polyp"}}),
        ),
        (
            findings_routes._resolve_kb_finding_classification_names,
            "colon_polyp",
            _lookup(findings={"colon_polyp": {"classifications": "polyp_size"}}),
        ),
        (
            findings_routes._resolve_kb_classification_choice_names,
            "polyp_size",
            _lookup(
                classifications={"polyp_size": {"classification_choices": "small"}}
            ),
        ),
        (
            indications_routes._resolve_kb_finding_names,
            "colonoscopy",
            _lookup(examinations={"colonoscopy": {"findings": "colon_polyp"}}),
        ),
        (
            indications_routes._resolve_exam_kb_indication_names,
            "colonoscopy",
            _lookup(examinations={"colonoscopy": {"indications": "screening"}}),
        ),
    ],
)
def test_resolution_helpers_fail_closed_for_malformed_relation_collections(
    monkeypatch: pytest.MonkeyPatch,
    resolver: Any,
    record_name: str,
    lookup: dict[str, dict[str, dict[str, Any]]],
) -> None:
    monkeypatch.setattr(
        findings_routes,
        "_kb_lookup",
        lambda *args, **kwargs: lookup,
    )

    assert (
        resolver(
            SimpleNamespace(name=record_name),
            module_name="malformed_module",
            version="1.0.0",
        )
        == set()
    )


def test_resolution_helpers_preserve_explicit_empty_and_populated_allowlists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        findings_routes,
        "_kb_lookup",
        lambda *args, **kwargs: _lookup(
            examinations={
                "colonoscopy": {
                    "findings": ["colon-polyp"],
                    "indications": [],
                }
            },
            findings={"colon_polyp": {"classifications": ["polyp size"]}},
            classifications={"polyp_size": {"classification_choices": ["small-polyp"]}},
        ),
    )

    examination = SimpleNamespace(name="colonoscopy")
    assert findings_routes._resolve_exam_kb_finding_names(
        examination, module_name="catalog", version="1.0.0"
    ) == {"colon_polyp"}
    assert findings_routes._resolve_kb_finding_classification_names(
        SimpleNamespace(name="colon_polyp"),
        module_name="catalog",
        version="1.0.0",
    ) == {"polyp_size"}
    assert findings_routes._resolve_kb_classification_choice_names(
        SimpleNamespace(name="polyp_size"),
        module_name="catalog",
        version="1.0.0",
    ) == {"small_polyp"}
    assert (
        indications_routes._resolve_exam_kb_indication_names(
            examination, module_name="catalog", version="1.0.0"
        )
        == set()
    )


def test_empty_classification_allowlist_does_not_expose_orm_classifications() -> None:
    classification = SimpleNamespace(
        id=1,
        name="host_only_classification",
        description="Not present in the selected KB",
        choices=_Relation(),
        classification_types=_Relation(),
    )
    finding = SimpleNamespace(
        id=2,
        name="colon_polyp",
        description="Polyp",
        finding_classifications=_Relation([classification]),
    )

    serialized = findings_routes._serialize_finding(
        finding,
        allowed_classification_names=set(),
        required_classification_names=set(),
    )

    assert serialized["classifications"] == []
    assert serialized["FindingClassifications"] == []


def test_explicit_catalog_module_requires_explicit_version() -> None:
    with pytest.raises(_ApiError) as exc_info:
        findings_routes._resolve_catalog_kb_identity(
            module_name="dgvs_reporting",
            module_version=None,
            orm_models=lambda: {},
            patient_examination_id=None,
            api_error=_api_error,
        )

    assert exc_info.value.status == 409
    assert exc_info.value.code == "knowledge-base-identity-required"


def test_explicit_catalog_identity_must_match_pinned_patient_examination() -> None:
    patient_examination = SimpleNamespace(
        knowledge_base_module="dgvs_reporting",
        knowledge_base_version="0.1.0",
    )

    with pytest.raises(_ApiError) as exc_info:
        findings_routes._resolve_catalog_kb_identity(
            module_name="star_upper_gi",
            module_version="0.1.2",
            orm_models=_orm_models_for_patient_examination(patient_examination),
            patient_examination_id=17,
            api_error=_api_error,
        )

    assert exc_info.value.status == 409
    assert exc_info.value.code == "knowledge-base-identity-conflict"


def test_explicit_catalog_identity_rejects_unpinned_patient_examination() -> None:
    patient_examination = SimpleNamespace(
        knowledge_base_module=None,
        knowledge_base_version=None,
    )

    with pytest.raises(_ApiError) as exc_info:
        findings_routes._resolve_catalog_kb_identity(
            module_name="dgvs_reporting",
            module_version="1.0.0",
            patient_examination_id=42,
            orm_models=_orm_models_for_patient_examination(patient_examination),
            api_error=_api_error,
        )

    assert exc_info.value.status == 409
    assert exc_info.value.code == "knowledge-base-identity-conflict"


def test_explicit_catalog_identity_accepts_matching_patient_examination() -> None:
    patient_examination = SimpleNamespace(
        knowledge_base_module="dgvs_reporting",
        knowledge_base_version="0.1.0",
    )

    assert findings_routes._resolve_catalog_kb_identity(
        module_name="dgvs_reporting",
        module_version="0.1.0",
        orm_models=_orm_models_for_patient_examination(patient_examination),
        patient_examination_id=17,
        api_error=_api_error,
    ) == ("dgvs_reporting", "0.1.0")
