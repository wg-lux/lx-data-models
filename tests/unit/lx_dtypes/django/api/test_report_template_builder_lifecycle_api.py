import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import yaml
from django.test import Client
from pytest import MonkeyPatch

from lx_dtypes.django.api import main as api_main
from lx_dtypes.django.api import report_template_builder
from lx_dtypes.models.interface.KnowledgeBaseResolver import (
    clear_knowledge_base_resolver_caches,
    load_knowledge_base,
)


@pytest.fixture(autouse=True)
def builder_route_authorization(monkeypatch: MonkeyPatch) -> None:
    """Keep lifecycle tests focused on builder behavior after route auth."""
    monkeypatch.setattr(
        api_main, "_authenticate_request_user", lambda request: object()
    )
    monkeypatch.setattr(
        api_main,
        "_report_template_access_allowed",
        lambda actor, capability: True,
    )


@pytest.fixture
def builder_terminology_registry(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> Iterator[None]:
    registry_path = tmp_path / "kb_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "active": {
                    "module_name": "builder_module",
                    "version": "1.0.0",
                },
                "modules": {
                    "builder_module": {
                        "1.0.0": {"input_dirs": [str(tmp_path)]},
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))
    clear_knowledge_base_resolver_caches()
    yield
    clear_knowledge_base_resolver_caches()


def test_builder_save_publish_and_unpublish_flow(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    builder_terminology_registry: None,
) -> None:
    del builder_terminology_registry
    module_dir = tmp_path / "builder_module"
    module_dir.mkdir(parents=True)
    (module_dir / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "name": "builder_module",
                "version": "1.0.0",
                "modules": [],
                "depends_on": [],
                "data": {"files": ["./kb.yaml"]},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (module_dir / "kb.yaml").write_text(
        yaml.safe_dump(
            [
                {"model": "finding", "name": "esophagus_polyp", "classifications": []},
                {
                    "model": "examination",
                    "name": "star_upper_gi_endoscopy",
                    "findings": ["esophagus_polyp"],
                },
            ],
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(report_template_builder, "MODULES_ROOT", tmp_path)

    client = Client()
    save_response = client.post(
        "/base_api/report-templates/builder/templates",
        data=json.dumps(
            {
                "module_name": "builder_module",
                "module_version": "1.0.0",
                "file_name": "custom_template",
                "template_name": "custom_template",
                "examination": "star_upper_gi_endoscopy",
                "sections": [
                    {
                        "section_type": "findings",
                        "name": "baseline",
                        "findings": [
                            {
                                "finding": "esophagus_polyp",
                                "required": True,
                                "multiple_allowed": False,
                                "classifications": [],
                                "validator": {"enabled": False},
                            }
                        ],
                    }
                ],
            }
        ),
        content_type="application/json",
        secure=True,
    )
    assert save_response.status_code == 200
    save_payload = save_response.json()
    assert save_payload["lifecycle_status"] == "draft"
    assert save_payload["readiness"]["can_publish"] is True

    list_response = client.get(
        "/base_api/report-templates/by-examination/builder_module/star_upper_gi_endoscopy?version=1.0.0",
        secure=True,
    )
    assert list_response.status_code == 200
    assert list_response.json() == []

    builder_list_response = client.get(
        "/base_api/report-templates/builder/by-examination/builder_module/star_upper_gi_endoscopy?version=1.0.0",
        secure=True,
    )
    assert builder_list_response.status_code == 200
    assert [item["name"] for item in builder_list_response.json()] == [
        "custom_template"
    ]
    assert builder_list_response.json()[0]["lifecycle_status"] == "draft"

    preview_response = client.get(
        "/base_api/report-templates/builder_module/custom_template/preview?version=1.0.0",
        secure=True,
    )
    assert preview_response.status_code == 200
    assert preview_response.json()["lifecycle_status"] == "draft"

    publish_response = client.post(
        "/base_api/report-templates/builder/templates/builder_module/custom_template/publish?version=1.0.0",
        secure=True,
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["lifecycle_status"] == "published"

    published_response = client.get(
        "/base_api/report-templates/builder_module/custom_template?version=1.0.0",
        secure=True,
    )
    assert published_response.status_code == 200
    assert published_response.json()["lifecycle_status"] == "published"

    unpublish_response = client.post(
        "/base_api/report-templates/builder/templates/builder_module/custom_template/unpublish?version=1.0.0",
        secure=True,
    )
    assert unpublish_response.status_code == 200
    assert unpublish_response.json()["lifecycle_status"] == "draft"

    after_unpublish = client.get(
        "/base_api/report-templates/builder_module/custom_template?version=1.0.0",
        secure=True,
    )
    assert after_unpublish.status_code == 404


def test_builder_module_kb_loader_uses_resolved_version(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    module_dir = tmp_path / "builder_module"
    module_dir.mkdir(parents=True)
    (module_dir / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "name": "builder_module",
                "version": "1.0.0",
                "modules": [],
                "depends_on": [],
                "data": {"files": ["./kb.yaml"]},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (module_dir / "kb.yaml").write_text(
        yaml.safe_dump(
            [
                {"model": "finding", "name": "esophagus_polyp", "classifications": []},
                {
                    "model": "examination",
                    "name": "star_upper_gi_endoscopy",
                    "findings": ["esophagus_polyp"],
                },
            ],
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    captured: dict[str, str | None] = {}

    monkeypatch.setattr(
        api_main,
        "_resolve_report_template_module_location",
        lambda module_name, version: (
            report_template_builder.ReportTemplateModuleLocation(
                module_name=module_name,
                version=version,
                modules_root=tmp_path,
            )
        ),
    )

    def _fake_load_knowledge_base(
        module_name: str,
        *,
        version: str | None = None,
        input_dirs: list[Path] | None = None,
    ) -> Any:
        del input_dirs
        captured["module_name"] = module_name
        captured["version"] = version
        return load_knowledge_base(module_name, version=version, input_dirs=[tmp_path])

    monkeypatch.setattr(
        api_main,
        "_load_module_kb",
        _fake_load_knowledge_base,
    )

    client = Client()
    response = client.post(
        "/base_api/report-templates/builder/templates",
        data=json.dumps(
            {
                "module_name": "builder_module",
                "module_version": "1.0.0",
                "file_name": "resolved_version_template",
                "template_name": "resolved_version_template",
                "examination": "star_upper_gi_endoscopy",
                "sections": [],
            }
        ),
        content_type="application/json",
        secure=True,
    )

    assert response.status_code == 200
    assert captured == {"module_name": "builder_module", "version": "1.0.0"}
