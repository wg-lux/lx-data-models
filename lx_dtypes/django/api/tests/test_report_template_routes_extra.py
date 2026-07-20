from __future__ import annotations

import json
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any
from pathlib import Path

import pytest
from django.test import Client

from lx_dtypes.django.api import main as api_main
from lx_dtypes.django.api import report_template_routes
from lx_dtypes.django.api import report_template_builder
from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination


@dataclass
class _CompiledSummary:
    can_publish: bool
    lifecycle_status: str = "draft"
    can_preview: bool = True

    def model_dump(self, mode: str = "json") -> dict[str, Any]:
        del mode
        return {
            "can_publish": self.can_publish,
            "lifecycle_status": self.lifecycle_status,
            "can_preview": self.can_preview,
            "errors": [],
            "warnings": [],
        }


class _FakeKb:
    def __init__(self) -> None:
        self.report_template: dict[str, Any] = {}
        self.findings_validator: dict[str, Any] = {}
        self.classification_validator: dict[str, Any] = {}
        self.intervention_validator: dict[str, Any] = {}
        self.unit_validator: dict[str, Any] = {}
        self.examination_validator: dict[str, Any] = {}

    def export_report_template(self, name: str) -> dict[str, Any]:
        if name not in self.report_template:
            raise KeyError(name)
        return {"name": name}

    def export_report_template_preview(self, name: str) -> dict[str, Any]:
        if name not in self.report_template:
            raise KeyError(name)
        return {"name": name, "lifecycle_status": "draft"}

    def evaluate_findings_validator(
        self, name: str, p_examination: PExamination
    ) -> dict[str, Any]:
        del p_examination
        return {"name": name, "kind": "findings"}

    def evaluate_classification_validator(
        self, name: str, p_examination: PExamination
    ) -> dict[str, Any]:
        del p_examination
        return {"name": name, "kind": "classification"}

    def evaluate_intervention_validator(
        self, name: str, p_examination: PExamination
    ) -> dict[str, Any]:
        del p_examination
        return {"name": name, "kind": "intervention"}

    def evaluate_unit_validator(
        self, name: str, p_examination: PExamination
    ) -> dict[str, Any]:
        del p_examination
        return {"name": name, "kind": "unit"}

    def evaluate_examination_validator(
        self, name: str, p_examination: PExamination
    ) -> dict[str, Any]:
        del p_examination
        return {"name": name, "kind": "examination"}


@pytest.fixture
def client() -> Client:
    return Client()


def test_save_report_template_returns_400_for_unknown_module(client: Client) -> None:
    response = client.post(
        "/base_api/report-templates/builder/templates",
        data=json.dumps(
            {
                "module_name": "missing_module",
                "file_name": "custom_template",
                "template_name": "custom_template",
                "examination": "star_upper_gi_endoscopy",
                "sections": [{"section_type": "patient_info", "name": "patient"}],
            }
        ),
        content_type="application/json",
        secure=True,
    )

    assert response.status_code == 400
    assert "Unknown report-template module" in response.content.decode()


def test_save_report_template_uses_resolver_input_dirs(
    client: Client, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: dict[str, Any] = {}
    module_dir = tmp_path / "builder_module"
    module_dir.mkdir(parents=True)
    (module_dir / "config.yaml").write_text(
        "\n".join(
            [
                "name: builder_module",
                "version: 1.0.0",
                "modules: []",
                "depends_on: []",
                "data:",
                "  files: []",
                "",
            ]
        ),
        encoding="utf-8",
    )

    def _fake_load_knowledge_base(
        module_name: str,
        *,
        version: str | None = None,
        input_dirs: list[Path] | None = None,
    ) -> _FakeKb:
        captured["module_name"] = module_name
        captured["version"] = version
        captured["input_dirs"] = input_dirs
        return _FakeKb()

    monkeypatch.setattr(
        report_template_routes, "load_knowledge_base", _fake_load_knowledge_base
    )
    monkeypatch.setattr(
        report_template_builder,
        "MODULES_ROOT",
        tmp_path,
    )
    monkeypatch.setattr(
        report_template_routes,
        "register_runtime_lookup_tracker",
        lambda kb: None,
    )
    monkeypatch.setattr(
        report_template_routes,
        "_compile_report_template",
        lambda *args, **kwargs: {"summary": _CompiledSummary(can_publish=True)},
    )

    response = client.post(
        "/base_api/report-templates/builder/templates",
        data=json.dumps(
            {
                "module_name": "builder_module",
                "file_name": "custom_template",
                "template_name": "custom_template",
                "examination": "star_upper_gi_endoscopy",
                "sections": [{"section_type": "patient_info", "name": "patient"}],
            }
        ),
        content_type="application/json",
        secure=True,
    )

    assert response.status_code == 200
    assert captured == {
        "module_name": "builder_module",
        "version": "1.0.0",
        "input_dirs": [tmp_path],
    }


def test_publish_report_template_returns_409_when_summary_blocks_publish(
    client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_kb = _FakeKb()
    fake_kb.report_template["blocked_template"] = object()
    monkeypatch.setattr(api_main, "_load_module_kb", lambda *args, **kwargs: fake_kb)
    monkeypatch.setattr(
        api_main,
        "_clear_kb_caches",
        lambda: None,
    )
    monkeypatch.setattr(
        report_template_routes,
        "_compile_report_template",
        lambda *args, **kwargs: {"summary": _CompiledSummary(can_publish=False)},
    )

    response = client.post(
        "/base_api/report-templates/builder/templates/report_template_examples/blocked_template/publish",
        secure=True,
    )

    assert response.status_code == 409
    assert "cannot be published" in response.content.decode()


def test_unpublish_report_template_returns_404_when_template_missing(
    client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(api_main, "_load_module_kb", lambda *args, **kwargs: _FakeKb())

    response = client.post(
        "/base_api/report-templates/builder/templates/report_template_examples/missing_template/unpublish",
        secure=True,
    )

    assert response.status_code == 404
    assert "missing_template" in response.content.decode()


def test_report_templates_by_examination_filters_unpublished_and_unready_templates(
    client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    class _Template:
        def __init__(self, examination: str) -> None:
            self.examination = examination

    class _Kb(_FakeKb):
        def __init__(self) -> None:
            super().__init__()
            self.report_template = {
                "published_ready": _Template("colonoscopy"),
                "draft_template": _Template("colonoscopy"),
                "published_blocked": _Template("colonoscopy"),
                "other_exam": _Template("gastroscopy"),
            }

        def get_report_template_lifecycle_status(self, name: str) -> str:
            return {
                "published_ready": "published",
                "draft_template": "draft",
                "published_blocked": "published",
                "other_exam": "published",
            }[name]

        def export_report_template(self, name: str) -> dict[str, Any]:
            return {"name": name}

    monkeypatch.setattr(api_main, "_load_module_kb", lambda *args, **kwargs: _Kb())
    monkeypatch.setattr(
        report_template_routes,
        "_compile_report_template",
        lambda kb, template_name, mode: {
            "summary": _CompiledSummary(can_publish=template_name == "published_ready")
        },
    )

    response = client.get(
        "/base_api/report-templates/by-examination/report_template_examples/colonoscopy",
        secure=True,
    )

    assert response.status_code == 200
    assert response.json() == [{"name": "published_ready"}]


def test_preview_and_definition_validation_return_404_for_missing_template(
    client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(api_main, "_load_module_kb", lambda *args, **kwargs: _FakeKb())

    preview = client.get(
        "/base_api/report-templates/report_template_examples/missing_template/preview",
        secure=True,
    )
    assert preview.status_code == 404

    definition = client.get(
        "/base_api/report-templates/report_template_examples/missing_template/validate-definition",
        secure=True,
    )
    assert definition.status_code == 404


def test_validate_from_ledger_returns_422_when_payload_build_fails(
    client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    class _FilterResult:
        def first(self) -> Any:
            return SimpleNamespace(id=5)

    class _Objects:
        def filter(self, **kwargs: Any) -> _FilterResult:
            del kwargs
            return _FilterResult()

    class _PatientExaminationModel:
        objects = _Objects()

    monkeypatch.setattr(
        api_main,
        "_orm_models",
        lambda: {"PatientExamination": _PatientExaminationModel},
    )
    monkeypatch.setattr(
        api_main,
        "_build_p_examination_payload_from_host_ledger",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            ValueError("cannot build payload")
        ),
    )

    response = client.post(
        "/base_api/report-templates/report_template_examples/star_upper_gi_main/validate-from-ledger/5",
        data=json.dumps({}),
        content_type="application/json",
        secure=True,
    )

    assert response.status_code == 422
    assert "cannot build payload" in response.content.decode()


@pytest.mark.parametrize(
    ("validator_kind", "registry_attr", "expected_kind"),
    [
        ("findings_validator", "findings_validator", "findings"),
        ("classification_validator", "classification_validator", "classification"),
        ("intervention_validator", "intervention_validator", "intervention"),
        ("unit_validator", "unit_validator", "unit"),
        ("examination_validator", "examination_validator", "examination"),
    ],
)
def test_single_validator_runtime_supports_all_validator_kinds(
    client: Client,
    monkeypatch: pytest.MonkeyPatch,
    validator_kind: str,
    registry_attr: str,
    expected_kind: str,
) -> None:
    fake_kb = _FakeKb()
    getattr(fake_kb, registry_attr)["demo_validator"] = object()
    monkeypatch.setattr(api_main, "_load_module_kb", lambda *args, **kwargs: fake_kb)

    response = client.post(
        f"/base_api/validators/report_template_examples/{validator_kind}/demo_validator/validate",
        data=json.dumps({"patient": "p", "examination": "e", "patient_findings": []}),
        content_type="application/json",
        secure=True,
    )

    assert response.status_code == 200
    assert response.json()["kind"] == expected_kind


def test_single_validator_runtime_returns_404_for_unknown_kind(
    client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(api_main, "_load_module_kb", lambda *args, **kwargs: _FakeKb())

    response = client.post(
        "/base_api/validators/report_template_examples/not_a_kind/demo/validate",
        data=json.dumps({"patient": "p", "examination": "e", "patient_findings": []}),
        content_type="application/json",
        secure=True,
    )

    assert response.status_code == 404
    assert "Unknown validator kind" in response.content.decode()
