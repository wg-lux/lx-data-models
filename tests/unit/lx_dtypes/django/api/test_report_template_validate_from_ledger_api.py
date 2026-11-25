import json
from typing import Any, ClassVar

import pytest
from django.test import Client

from lx_dtypes.django.api import main as api_main
from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination


class _FilterResult:
    def __init__(self, value: Any) -> None:
        self._value = value

    def first(self) -> Any:
        return self._value


class _Objects:
    def __init__(self, value: Any) -> None:
        self._value = value

    def filter(self, **kwargs: Any) -> _FilterResult:
        if self._value is None:
            return _FilterResult(None)
        requested_id = kwargs.get("id")
        if requested_id is None or requested_id == getattr(self._value, "id", None):
            return _FilterResult(self._value)
        return _FilterResult(None)


class _PatientExaminationModel:
    def __init__(self, value: Any) -> None:
        self.objects = _Objects(value)


class _FakeEmptyFindingsQueryset:
    def filter(self, **kwargs: Any) -> list[Any]:
        del kwargs
        return []


class _FakeRelation:
    def __init__(self, values: list[Any]) -> None:
        self._values = values

    def filter(self, **kwargs: Any) -> "_FakeRelation":
        del kwargs
        return self

    def select_related(self, *fields: str) -> "_FakeRelation":
        del fields
        return self

    def all(self) -> list[Any]:
        return self._values


class _FakeFindingsQueryset:
    def __init__(self, values: list[Any]) -> None:
        self._values = values

    def filter(self, **kwargs: Any) -> list[Any]:
        assert kwargs == {"patient_examination_id": 101}
        return self._values


def test_build_p_examination_payload_from_host_ledger_without_findings(
    monkeypatch: Any,
) -> None:
    class _Exam:
        name = "colonoscopy"

    class _PatientExam:
        id = 101
        patient_id = 202
        examination = _Exam()
        examination_safe = _Exam()
        knowledge_base_module = "report_template_examples"
        knowledge_base_version = "0.1.0"
        examiners: ClassVar[list[Any]] = []

    monkeypatch.setattr(
        api_main,
        "_active_patient_findings_queryset",
        lambda: _FakeEmptyFindingsQueryset(),
    )

    payload = api_main._build_p_examination_payload_from_host_ledger(
        _PatientExam(), route_module_name="report_template_examples"
    )

    assert payload.examination == "colonoscopy"
    assert payload.patient == "202"
    assert payload.knowledge_base_module == "report_template_examples"
    assert payload.knowledge_base_version == "0.1.0"
    assert payload.patient_findings == []


def test_build_p_examination_payload_uses_canonical_examination_reference(
    monkeypatch: Any,
) -> None:
    class _Exam:
        name = "colonoscopy"

    class _PatientExam:
        id = 101
        patient_id = 202
        examination = _Exam()
        examination_safe = _Exam()
        knowledge_base_module = "report_template_examples"
        knowledge_base_version = "0.1.0"
        examiners: ClassVar[list[Any]] = []

    class _Finding:
        name = "colon_polyp"

    class _PatientFinding:
        id = 303
        instance_id = 1
        finding = _Finding()
        classifications = _FakeRelation([])
        interventions = _FakeRelation([])

    monkeypatch.setattr(
        api_main,
        "_active_patient_findings_queryset",
        lambda: _FakeFindingsQueryset([_PatientFinding()]),
    )

    payload = api_main._build_p_examination_payload_from_host_ledger(
        _PatientExam(), route_module_name="report_template_examples"
    )

    assert len(payload.patient_findings) == 1
    assert payload.patient_findings[0].patient_examination == payload.examination


def _indication_patient_exam(indication_rows: list[Any] | None) -> Any:
    class _Exam:
        name = "colonoscopy"

    class _PatientExam:
        id = 101
        patient_id = 202
        examination = _Exam()
        examination_safe = _Exam()
        knowledge_base_module = "report_template_examples"
        knowledge_base_version = "0.1.0"
        examiners: ClassVar[list[Any]] = []

    patient_exam = _PatientExam()
    if indication_rows is not None:
        patient_exam.indications = _FakeRelation(indication_rows)  # type: ignore[attr-defined]
    return patient_exam


def _named(name: str, **attrs: Any) -> Any:
    return type("_Named", (), {"name": name, **attrs})()


def test_build_p_examination_payload_projects_host_indications(
    monkeypatch: Any,
) -> None:
    # Required indication concepts read patient_indications; saved host
    # indications must therefore reach the ledger record.
    monkeypatch.setattr(
        api_main,
        "_active_patient_findings_queryset",
        lambda: _FakeEmptyFindingsQueryset(),
    )
    choice = _named("sedation_planned", classification=_named("sedation"))
    rows = [
        type(
            "_Row",
            (),
            {
                "pk": 7,
                "examination_indication": _named("colonoscopy_screening"),
                "indication_choice": None,
            },
        )(),
        type(
            "_Row",
            (),
            {
                "pk": 8,
                "examination_indication": _named("colonoscopy_generic"),
                "indication_choice": choice,
            },
        )(),
    ]

    payload = api_main._build_p_examination_payload_from_host_ledger(
        _indication_patient_exam(rows), route_module_name="report_template_examples"
    )

    assert [item.indication for item in payload.patient_indications] == [
        "colonoscopy_screening",
        "colonoscopy_generic",
    ]
    assert all(
        item.patient_examination == "colonoscopy"
        for item in payload.patient_indications
    )
    assert payload.patient_indications[0].patient_indication_classifications == []
    classification = payload.patient_indications[1].patient_indication_classifications[
        0
    ]
    assert (classification.classification, classification.classification_choice) == (
        "sedation",
        "sedation_planned",
    )
    assert classification.patient_indication == str(payload.patient_indications[1].uuid)
    rebuilt = api_main._build_p_examination_payload_from_host_ledger(
        _indication_patient_exam(rows), route_module_name="report_template_examples"
    )
    assert [str(item.uuid) for item in rebuilt.patient_indications] == [
        str(item.uuid) for item in payload.patient_indications
    ]


def _choice_row(pk: int, indication: Any, choice: Any) -> Any:
    return type(
        "_Row",
        (),
        {"pk": pk, "examination_indication": indication, "indication_choice": choice},
    )()


def test_build_p_examination_payload_resolves_many_to_many_choice_classification(
    monkeypatch: Any,
) -> None:
    # endoreg-db links choices to classifications many-to-many; the selected
    # classification is the one the choice shares with its indication.
    monkeypatch.setattr(
        api_main,
        "_active_patient_findings_queryset",
        lambda: _FakeEmptyFindingsQueryset(),
    )
    choice = _named(
        "sedation_planned",
        classifications=_FakeRelation([_named("sedation"), _named("other_use")]),
    )
    indication = _named(
        "colonoscopy_generic", classifications=_FakeRelation([_named("sedation")])
    )

    payload = api_main._build_p_examination_payload_from_host_ledger(
        _indication_patient_exam([_choice_row(5, indication, choice)]),
        route_module_name="report_template_examples",
    )

    classification = payload.patient_indications[0].patient_indication_classifications[
        0
    ]
    assert classification.classification == "sedation"


def test_build_p_examination_payload_rejects_non_iterable_classification_relation(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        api_main,
        "_active_patient_findings_queryset",
        lambda: _FakeEmptyFindingsQueryset(),
    )
    relation = type("_InvalidRelation", (), {"all": lambda self: None})()
    choice = _named("sedation_planned", classifications=relation)
    indication = _named("colonoscopy_generic", classifications=relation)
    with pytest.raises(TypeError, match="must return an iterable"):
        api_main._build_p_examination_payload_from_host_ledger(
            _indication_patient_exam([_choice_row(5, indication, choice)]),
            route_module_name="report_template_examples",
        )


def test_build_p_examination_payload_rejects_unresolvable_choice_classification(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        api_main,
        "_active_patient_findings_queryset",
        lambda: _FakeEmptyFindingsQueryset(),
    )
    shared = _FakeRelation([_named("sedation"), _named("other_use")])
    choice = _named("sedation_planned", classifications=shared)
    indication = _named("colonoscopy_generic", classifications=shared)

    with pytest.raises(ValueError, match="exactly one classification"):
        api_main._build_p_examination_payload_from_host_ledger(
            _indication_patient_exam([_choice_row(6, indication, choice)]),
            route_module_name="report_template_examples",
        )


def test_build_p_examination_payload_without_host_indication_relation(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        api_main,
        "_active_patient_findings_queryset",
        lambda: _FakeEmptyFindingsQueryset(),
    )

    payload = api_main._build_p_examination_payload_from_host_ledger(
        _indication_patient_exam(None), route_module_name="report_template_examples"
    )

    assert payload.patient_indications == []


def test_build_p_examination_payload_rejects_unnamed_host_indication(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        api_main,
        "_active_patient_findings_queryset",
        lambda: _FakeEmptyFindingsQueryset(),
    )
    rows = [
        type(
            "_Row",
            (),
            {"pk": 9, "examination_indication": None, "indication_choice": None},
        )()
    ]

    with pytest.raises(ValueError, match="without an indication name"):
        api_main._build_p_examination_payload_from_host_ledger(
            _indication_patient_exam(rows), route_module_name="report_template_examples"
        )


def test_validate_report_template_runtime_from_ledger_not_found(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        api_main,
        "_orm_models",
        lambda: {"PatientExamination": _PatientExaminationModel(None)},
    )

    client = Client()
    response = client.post(
        (
            "/base_api/report-templates/report_template_examples/"
            "star_upper_gi_main/validate-from-ledger/999999?version=0.1.0"
        ),
        content_type="application/json",
        secure=True,
    )

    assert response.status_code == 404
    assert "PatientExamination '999999' not found." in response.content.decode()


def test_validate_report_template_runtime_from_ledger_success(
    monkeypatch: Any,
) -> None:
    class _Exam:
        name = "star_upper_gi_endoscopy"

    class _PatientExam:
        id = 7
        patient_id = 11
        examination = _Exam()
        examination_safe = _Exam()
        knowledge_base_module = "report_template_examples"
        knowledge_base_version = "0.1.0"
        examiners: ClassVar[list[Any]] = []

    class _FakeKnowledgeBase:
        class _Config:
            name = "report_template_examples"
            version = "0.1.0"

            def model_dump(self, *, mode: str) -> dict[str, str]:
                assert mode == "json"
                return {"name": "report_template_examples", "version": "0.1.0"}

        config = _Config()

        def model_dump(self, *, mode: str) -> dict[str, object]:
            assert mode == "json"
            return {"config": {"name": "report_template_examples", "version": "0.1.0"}}

        def export_report_template(self, name: str) -> dict[str, Any]:
            return {
                "name": name,
                "version": "1.0.0",
                "coverage_version": "report_concept_coverage_v1",
                "coverage_concepts": [
                    {
                        "concept_id": "examination.findings",
                        "label": "Findings",
                        "applicability_status": "required",
                        "validator_names": ["findings_validator"],
                        "evidence_path": ["patient_findings"],
                        "concept_value_path": ["examination"],
                        "allowed_values": ["star_upper_gi_endoscopy"],
                    }
                ],
            }

        def evaluate_report_template_validators(
            self, name: str, p_examination: PExamination, *, language: str = "de"
        ) -> dict[str, Any]:
            assert name == "star_upper_gi_main"
            assert p_examination.examination == "star_upper_gi_endoscopy"
            return {
                "template_name": name,
                "ok": True,
                "evaluated_findings_count": 0,
                "findings_validators": [],
                "classification_validators": [],
                "intervention_validators": [],
                "unit_validators": [],
                "examination_validators": [],
                "issues": [],
            }

    monkeypatch.setattr(
        api_main,
        "_orm_models",
        lambda: {"PatientExamination": _PatientExaminationModel(_PatientExam())},
    )
    monkeypatch.setattr(
        api_main,
        "_active_patient_findings_queryset",
        lambda: _FakeEmptyFindingsQueryset(),
    )
    monkeypatch.setattr(
        api_main, "_load_module_kb", lambda *args, **kwargs: _FakeKnowledgeBase()
    )

    client = Client()
    response = client.post(
        (
            "/base_api/report-templates/report_template_examples/"
            "star_upper_gi_main/validate-from-ledger/7?version=0.1.0"
        ),
        data=json.dumps({}),
        content_type="application/json",
        secure=True,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["template_name"] == "star_upper_gi_main"
    assert payload["ok"] is True
    assert payload["knowledge_base_module"] == "report_template_examples"
    assert payload["knowledge_base_version"] == "0.1.0"
    assert (
        payload["concept_coverage"]["identity"]["template_name"] == "star_upper_gi_main"
    )


def _descriptor_host_fixture():
    from types import SimpleNamespace
    from uuid import uuid4

    from lx_dtypes.models.contracts.dtypes_record_persistence import (
        DtypesRecordPersistencePayload,
    )

    finding_uuid = str(uuid4())
    host = SimpleNamespace(
        id=101,
        patient_id=202,
        examination=SimpleNamespace(name="colonoscopy"),
        knowledge_base_module="test",
        knowledge_base_version="1.0",
        dtypes_record={},
    )
    choice = SimpleNamespace(
        id=1,
        classification=SimpleNamespace(name="histology"),
        classification_choice=SimpleNamespace(name="result"),
        numerical_descriptors={},
    )
    finding = SimpleNamespace(
        id=303,
        instance_id=finding_uuid,
        finding=SimpleNamespace(name="colon_polyp"),
        classifications=_FakeRelation([choice]),
        interventions=_FakeRelation([]),
    )
    record = DtypesRecordPersistencePayload.model_validate(
        {
            "patient": "202",
            "examination": "colonoscopy",
            "knowledge_base_module": "test",
            "knowledge_base_version": "1.0",
            "patient_findings": [
                {
                    "uuid": finding_uuid,
                    "finding": "colon_polyp",
                    "patient_examination": "colonoscopy",
                    "patient_finding_classifications": [
                        {
                            "patient_finding": finding_uuid,
                            "patient_finding_classification_choices": [
                                {
                                    "classification": "histology",
                                    "classification_choice": "result",
                                    "patient_finding_classifications": "group",
                                    "patient_finding_classification_choice_descriptors": [
                                        {
                                            "classification_choice_descriptor": name,
                                            "descriptor_value": value,
                                            "patient_finding_classification_choice": "choice",
                                        }
                                        for name, value in {
                                            "text": "local wording",
                                            "number": 3.5,
                                            "integer": 2,
                                            "boolean": False,
                                            "selection": ["one", "two"],
                                        }.items()
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
    )
    return host, finding, choice, record


def _rebuild_descriptor_fixture(host, finding, record=None):
    from lx_dtypes.django.api.findings_routes import (
        build_p_examination_payload_from_host_ledger,
    )

    return build_p_examination_payload_from_host_ledger(
        host,
        route_module_name="test",
        orm_models=dict,
        active_patient_findings_queryset=lambda: _FakeFindingsQueryset([finding]),
        descriptor_source=record,
    )


def test_canonical_descriptors_survive_persisted_ledger_rebuild():
    host, finding, _, record = _descriptor_host_fixture()
    first = _rebuild_descriptor_fixture(host, finding, record)
    host.dtypes_record = first.model_dump(mode="json")
    rebuilt = _rebuild_descriptor_fixture(host, finding)
    choices = (
        rebuilt.patient_findings[0]
        .patient_finding_classifications[0]
        .patient_finding_classification_choices
    )
    assert {
        item.classification_choice_descriptor: item.descriptor_value
        for item in choices[0].patient_finding_classification_choice_descriptors
    } == {
        "text": "local wording",
        "number": 3.5,
        "integer": 2,
        "boolean": False,
        "selection": ["one", "two"],
    }


def test_canonical_descriptors_do_not_cross_findings_or_choices():
    from uuid import uuid4

    host, finding, choice, record = _descriptor_host_fixture()
    host.dtypes_record = record.model_dump(mode="json")
    for finding_uuid, choice_name in [
        (str(uuid4()), "result"),
        (finding.instance_id, "changed"),
    ]:
        finding.instance_id = finding_uuid
        choice.classification_choice.name = choice_name
        rebuilt = _rebuild_descriptor_fixture(host, finding)
        assert (
            not rebuilt.patient_findings[0]
            .patient_finding_classifications[0]
            .patient_finding_classification_choices[0]
            .patient_finding_classification_choice_descriptors
        )
    finding.classifications = _FakeRelation([])
    assert (
        not _rebuild_descriptor_fixture(host, finding)
        .patient_findings[0]
        .patient_finding_classifications
    )


def test_canonical_descriptors_reject_wrong_identity_duplicates_and_conflicts():
    import pytest

    host, finding, _, record = _descriptor_host_fixture()
    host.dtypes_record = record.model_dump(mode="json")
    record.patient = "other"
    with pytest.raises(ValueError, match="identity"):
        _rebuild_descriptor_fixture(host, finding, record)
    record.patient = "202"
    descriptors = (
        record.patient_findings[0]
        .patient_finding_classifications[0]
        .patient_finding_classification_choices[0]
        .patient_finding_classification_choice_descriptors
    )
    descriptors.append(descriptors[0])
    with pytest.raises(ValueError, match="Duplicate"):
        _rebuild_descriptor_fixture(host, finding, record)
    descriptors.pop()
    descriptors[0].descriptor_value = "contradiction"
    with pytest.raises(ValueError, match="Conflicting"):
        _rebuild_descriptor_fixture(host, finding, record)


def test_descriptor_sources_merge_additions_but_reject_scalar_type_conflicts():
    import pytest

    host, finding, choice, record = _descriptor_host_fixture()
    stored = record.model_copy(deep=True)
    stored.patient_findings[0].patient_finding_classifications[
        0
    ].patient_finding_classification_choices[
        0
    ].patient_finding_classification_choice_descriptors.pop()
    host.dtypes_record = stored.model_dump(mode="json")
    rebuilt = _rebuild_descriptor_fixture(host, finding, record)
    assert (
        len(
            rebuilt.patient_findings[0]
            .patient_finding_classifications[0]
            .patient_finding_classification_choices[0]
            .patient_finding_classification_choice_descriptors
        )
        == 5
    )
    choice.numerical_descriptors = {"boolean": 0}
    with pytest.raises(ValueError, match="Conflicting host"):
        _rebuild_descriptor_fixture(host, finding, record)
