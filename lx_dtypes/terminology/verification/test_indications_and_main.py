from __future__ import annotations

import importlib
import json
from types import SimpleNamespace

import pytest

from lx_dtypes.django.api import indications_routes as routes
from lx_dtypes.terminology import terminology_loader as central
from lx_dtypes.terminology.terminology_service import TerminologyError


class ApiError(Exception):
    def __init__(self, status, code, message):
        self.status = status
        self.code = code
        super().__init__(message)


def api_error(status, code, message):
    raise ApiError(status, code, message)


class Rows(list):
    def all(self):
        return self

    def first(self):
        return self[0] if self else None

    def filter(self, **kwargs):
        return Rows(
            x for x in self if all(getattr(x, k, None) == v for k, v in kwargs.items())
        )


def set_active(storage, name, version):
    p = storage / "registry.json"
    value = json.loads(p.read_text())
    value["active"] = {"module_name": name, "version": version}
    p.write_text(json.dumps(value))


@pytest.fixture
def catalog_models(storage):
    kb = central.load_module_kb("dgvs_reporting", version="0.1.0")
    entry = next(
        x
        for x in kb.export_core_concepts()["examination"]
        if x["name"] == "colonoscopy"
    )
    indications = Rows(
        SimpleNamespace(
            id=i + 1,
            name=name,
            description=name,
            indication_types=Rows(),
            classifications=Rows(),
            interventions=Rows(),
        )
        for i, name in enumerate(entry["indications"])
    )
    invalid = SimpleNamespace(
        id=9999,
        name="not_in_this_kb",
        description="not allowed",
        indication_types=Rows(),
        classifications=Rows(),
        interventions=Rows(),
    )
    findings = Rows(
        SimpleNamespace(id=i + 1, name=name, description=name)
        for i, name in enumerate(entry["findings"])
    )
    findings.append(
        SimpleNamespace(id=9999, name="not_allowed", description="not allowed")
    )
    exam = SimpleNamespace(
        id=1,
        name="colonoscopy",
        description="Colonoscopy",
        indications=Rows([*indications, invalid]),
        get_available_findings=lambda: findings,
    )
    second = SimpleNamespace(
        id=2,
        name="colonoscopy",
        description="Colonoscopy",
        indications=exam.indications,
        get_available_findings=lambda: findings,
    )
    patient = SimpleNamespace(
        id=11,
        knowledge_base_module="dgvs_reporting",
        knowledge_base_version="0.1.0",
        examination_id=1,
        examination=exam,
    )
    models = {
        "Examination": SimpleNamespace(objects=Rows([exam, second])),
        "PatientExamination": SimpleNamespace(objects=Rows([patient])),
    }
    return models, entry, patient


def register(api, models):
    routes.register_indications_routes(
        api, orm_models=lambda: models, api_error=api_error
    )
    return api.routes


def test_indications_use_central_loader_with_exact_identity(
    storage, catalog_models, api, monkeypatch
):
    models, entry, _ = catalog_models
    handlers = register(api, models)
    calls = []
    original = routes.load_module_kb

    def counted(name, *, version=None):
        calls.append((name, version))
        return original(name, version=version)

    monkeypatch.setattr(routes, "load_module_kb", counted)
    result = handlers["/examinations/{examination_id}/indications/"](
        None, 1, module_name="dgvs_reporting", module_version="0.1.0"
    )
    assert {x["name"] for x in result} == set(entry["indications"])
    assert calls == [("dgvs_reporting", "0.1.0")]


def test_tree_loads_only_once_and_filters_both_relations(
    storage, catalog_models, api, monkeypatch
):
    models, entry, _ = catalog_models
    handlers = register(api, models)
    calls = []
    original = routes.load_module_kb
    set_active(storage, "dgvs_reporting", "0.1.0")

    def counted(name, *, version=None):
        calls.append((name, version))
        kb = original(name, version=version)
        # Simulate a concurrent active-selection change during this response.
        set_active(storage, "mst_3_0", "3.0.0")
        return kb

    monkeypatch.setattr(routes, "load_module_kb", counted)
    result = handlers["/indications/tree/"](None)
    assert {x["name"] for x in result} == set(entry["indications"])
    assert calls == [("dgvs_reporting", "0.1.0")]
    assert central.active_kb_identity() == ("mst_3_0", "3.0.0")
    for node in result:
        assert len(node["examinations"]) == 2
        for exam in node["examinations"]:
            assert {f["name"] for f in exam["findings"]} == set(entry["findings"])


def test_patient_pinned_identity_does_not_use_active_default(
    storage, catalog_models, api
):
    models, entry, _ = catalog_models
    handlers = register(api, models)
    assert central.active_kb_identity()[0] == "star_upper_gi"
    result = handlers["/indications/tree/"](None, patient_examination_id=11)
    assert {x["name"] for x in result} == set(entry["indications"])
    assert all(len(x["examinations"]) == 1 for x in result)


def test_patient_identity_conflict_is_rejected(storage, catalog_models, api):
    models, _, _ = catalog_models
    handlers = register(api, models)
    with pytest.raises(ApiError) as exc:
        handlers["/indications/tree/"](
            None,
            module_name="mst_3_0",
            module_version="3.0.0",
            patient_examination_id=11,
        )
    assert (exc.value.status, exc.value.code) == (
        409,
        "knowledge-base-identity-conflict",
    )


def test_missing_patient_identity_keeps_specific_error(storage, catalog_models, api):
    models, _, patient = catalog_models
    patient.knowledge_base_version = ""
    handlers = register(api, models)
    with pytest.raises(ApiError) as exc:
        handlers["/indications/tree/"](None, patient_examination_id=11)
    assert (exc.value.status, exc.value.code) == (
        409,
        "knowledge-base-identity-required",
    )


def test_patient_exam_relationship_is_checked(storage, catalog_models, api):
    models, _, _ = catalog_models
    handlers = register(api, models)
    with pytest.raises(ApiError) as exc:
        handlers["/examinations/{examination_id}/indications/"](
            None, 2, patient_examination_id=11
        )
    assert exc.value.status == 404


@pytest.mark.parametrize("name,version", [("dgvs_reporting", None), (None, "0.1.0")])
def test_half_identity_is_not_guessed(storage, catalog_models, api, name, version):
    models, _, _ = catalog_models
    handlers = register(api, models)
    with pytest.raises(ApiError) as exc:
        handlers["/indications/tree/"](None, module_name=name, module_version=version)
    assert exc.value.code == "knowledge-base-identity-required"


def test_central_errors_preserve_status(storage, catalog_models, api, monkeypatch):
    models, _, _ = catalog_models
    handlers = register(api, models)
    error = TerminologyError(500, "real service failure")

    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(routes, "load_module_kb", fail)
    with pytest.raises(TerminologyError) as exc:
        handlers["/indications/tree/"](
            None, module_name="dgvs_reporting", module_version="0.1.0"
        )
    assert exc.value is error


def test_missing_examination_still_404(storage, catalog_models, api):
    models, _, _ = catalog_models
    handlers = register(api, models)
    with pytest.raises(ApiError) as exc:
        handlers["/examinations/{examination_id}/indications/"](None, 99)
    assert exc.value.status == 404


def test_main_callbacks_resolve_to_the_same_hydrated_root(storage):
    main = importlib.import_module("lx_dtypes.django.api.main")
    main = importlib.reload(main)
    location = main._resolve_report_template_module_location("star_upper_gi", "0.1.2")
    kb = main._load_module_kb("star_upper_gi", "0.1.2")
    assert location.modules_root.is_relative_to(storage)
    assert kb.config.source_file.parent.parent == location.modules_root
    assert main.handle_terminology_error(None, TerminologyError(409, "conflict")) == (
        409,
        {"code": "terminology-error", "message": "conflict"},
    )
