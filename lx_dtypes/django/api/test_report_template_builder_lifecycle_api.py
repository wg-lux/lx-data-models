import json
import yaml
from pathlib import Path
from pytest import MonkeyPatch
from typing import Any
from django.test import Client
from lx_dtypes.django.api import main as api_main
from lx_dtypes.django.api import report_template_builder
from lx_dtypes.models.interface.KnowledgeBaseResolver import load_knowledge_base


def test_builder_save_publish_and_unpublish_flow(
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

    monkeypatch.setattr(report_template_builder, "MODULES_ROOT", tmp_path)
    monkeypatch.setattr(
        api_main,
        "_load_module_kb",
        lambda module_name, version=None: load_knowledge_base(
            module_name,
            version=version,
            input_dirs=[tmp_path],
        ),
    )

    client = Client()
    save_response = client.post(
        "/base_api/report-templates/builder/templates",
        data=json.dumps(
            {
                "module_name": "builder_module",
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
        "/base_api/report-templates/by-examination/builder_module/star_upper_gi_endoscopy",
        secure=True,
    )
    assert list_response.status_code == 200
    assert list_response.json() == []

    preview_response = client.get(
        "/base_api/report-templates/builder_module/custom_template/preview",
        secure=True,
    )
    assert preview_response.status_code == 200
    assert preview_response.json()["lifecycle_status"] == "draft"

    publish_response = client.post(
        "/base_api/report-templates/builder/templates/builder_module/custom_template/publish",
        secure=True,
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["lifecycle_status"] == "published"

    published_response = client.get(
        "/base_api/report-templates/builder_module/custom_template",
        secure=True,
    )
    assert published_response.status_code == 200
    assert published_response.json()["lifecycle_status"] == "published"

    unpublish_response = client.post(
        "/base_api/report-templates/builder/templates/builder_module/custom_template/unpublish",
        secure=True,
    )
    assert unpublish_response.status_code == 200
    assert unpublish_response.json()["lifecycle_status"] == "draft"

    after_unpublish = client.get(
        "/base_api/report-templates/builder_module/custom_template",
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

    monkeypatch.setattr(report_template_builder, "MODULES_ROOT", tmp_path)
    monkeypatch.setattr(
        api_main,
        "get_knowledge_base_identity",
        lambda module_name, *, version=None, input_dirs=None: (
            module_name,
            "1.0.0",
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

    monkeypatch.setattr(api_main, "load_knowledge_base", _fake_load_knowledge_base)

    client = Client()
    response = client.post(
        "/base_api/report-templates/builder/templates",
        data=json.dumps(
            {
                "module_name": "builder_module",
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
