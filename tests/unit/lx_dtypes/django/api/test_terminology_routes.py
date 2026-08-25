# ruff: noqa: FLY002 - line lists keep embedded YAML fixtures readable

from __future__ import annotations

import json
import zipfile
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from threading import Barrier
from typing import cast

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from ninja.errors import HttpError
from ninja.files import UploadedFile

from lx_dtypes.django.api import terminology_routes


@pytest.fixture(autouse=True)
def reset_active_terminology_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LX_DTYPES_KB_REGISTRY", raising=False)


def _write_module_config(
    module_dir: Path,
    *,
    name: str,
    version: str,
    medical_field: str | None = None,
    modules: list[str] | None = None,
    data_dirs: list[str] | None = None,
) -> None:
    module_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        f"name: {name}",
        'description: ""',
        f"version: {version}",
    ]
    if medical_field:
        lines.append(f"medical_field: {medical_field}")
    if modules:
        lines.extend(["modules:", *[f"  - {module}" for module in modules]])
    else:
        lines.append("modules: []")
    lines.append("depends_on: []")
    if data_dirs is not None:
        lines.append("data:")
        if data_dirs:
            lines.extend(["  dirs:", *[f"    - {data_dir}" for data_dir in data_dirs]])
        else:
            lines.append("  dirs: []")
    (module_dir / "config.yaml").write_text("\n".join(lines) + "\n")


def _write_unit(module_dir: Path, *, name: str) -> None:
    data_dir = module_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "units.yaml").write_text(
        "\n".join(
            [
                "- model: unit",
                f"  name: {name}",
                "  abbreviation: u",
            ]
        )
        + "\n"
    )


def _editor_bundle_zip() -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "published_terminology/config.yaml",
            "\n".join(
                [
                    "name: published_terminology",
                    'description: ""',
                    "version: 2026.05.04",
                    "medical_field: gastroenterology",
                    "modules:",
                    "  - lx_units",
                    "depends_on: []",
                ]
            )
            + "\n",
        )
        archive.writestr(
            "published_terminology/lx_units/config.yaml",
            "\n".join(
                [
                    "name: lx_units",
                    'description: ""',
                    "version: 2026.05.04",
                    "modules: []",
                    "depends_on: []",
                    "data:",
                    "  dirs:",
                    "    - ./data",
                ]
            )
            + "\n",
        )
        archive.writestr(
            "published_terminology/lx_units/data/units.yaml",
            "\n".join(
                [
                    "- model: unit",
                    "  name: imported_unit",
                    "  abbreviation: iu",
                ]
            )
            + "\n",
        )
    return buffer.getvalue()


def _bundle_zip_with_missing_transitive_dependency() -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "incomplete_bundle/config.yaml",
            "\n".join(
                [
                    "name: incomplete_bundle",
                    'description: ""',
                    "version: 1.0.0",
                    "modules:",
                    "  - child_module",
                    "depends_on: []",
                ]
            )
            + "\n",
        )
        archive.writestr(
            "incomplete_bundle/child_module/config.yaml",
            "\n".join(
                [
                    "name: child_module",
                    'description: ""',
                    "version: 1.0.0",
                    "modules: []",
                    "depends_on:",
                    "  - missing_dependency",
                ]
            )
            + "\n",
        )
    return buffer.getvalue()


def _bundle_zip_with_traversal_data_dir() -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "published_terminology/config.yaml",
            "\n".join(
                [
                    "name: published_terminology",
                    'description: ""',
                    "version: 2026.05.04",
                    "medical_field: gastroenterology",
                    "modules: []",
                    "depends_on: []",
                    "data:",
                    "  dirs:",
                    "    - ../../../etc",
                ]
            )
            + "\n",
        )
    return buffer.getvalue()


def _write_registry(tmp_path: Path, *, active: bool = False) -> Path:
    kb_root = tmp_path / "knowledge-bases"
    bundle_dir = kb_root / "published_terminology"
    _write_module_config(
        bundle_dir,
        name="published_terminology",
        version="2026.04.30",
        medical_field="gastroenterology",
        modules=["lx_units"],
        data_dirs=[],
    )
    units_dir = bundle_dir / "lx_units"
    _write_module_config(
        units_dir,
        name="lx_units",
        version="2026.04.30",
        data_dirs=["./data"],
    )
    _write_unit(units_dir, name="published_unit")

    registry_path = tmp_path / "kb_registry.json"
    payload: dict[str, object] = {
        "modules": {
            "published_terminology": {
                "2026.04.30": {
                    "input_dirs": [
                        str(kb_root),
                    ]
                }
            }
        }
    }
    if active:
        payload["active"] = {
            "module_name": "published_terminology",
            "version": "2026.04.30",
        }
    registry_path.write_text(json.dumps(payload))
    return registry_path


def test_list_terminology_bundles_reports_no_active_selection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    registry_path = _write_registry(tmp_path)
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))

    response = Client().get("/base_api/terminology/bundles", secure=True)

    assert response.status_code == 200
    payload = response.json()
    assert payload["revision"] == terminology_routes._registry_revision(registry_path)
    assert payload["active"] is None
    assert payload["bundles"] == [
        {
            "module_name": "published_terminology",
            "version": "2026.04.30",
            "medical_field": "gastroenterology",
            "is_active": False,
        }
    ]


def test_list_terminology_bundles_does_not_expose_storage_source(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source_url = (
        "https://github.com/wg-lux/lx-data-models/tree/main/demo-data/star_upper_gi"
    )
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(
        json.dumps(
            {"modules": {"star_upper_gi": {"0.1.1": {"input_dirs": [source_url]}}}}
        )
    )
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))

    response = Client().get("/base_api/terminology/bundles", secure=True)

    assert response.status_code == 200
    assert "input_dirs" not in response.json()["bundles"][0]


def test_select_terminology_bundle_sets_active_runtime_selection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    registry_path = _write_registry(tmp_path)
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))

    response = Client().post(
        "/base_api/terminology/bundles/select",
        data=json.dumps(
            {
                "module_name": "published_terminology",
                "version": "2026.04.30",
                "expected_revision": terminology_routes._registry_revision(
                    registry_path
                ),
            }
        ),
        content_type="application/json",
        secure=True,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["revision"] == terminology_routes._registry_revision(registry_path)
    assert payload["active"]["module_name"] == "published_terminology"
    assert payload["active"]["version"] == "2026.04.30"
    assert payload["active"]["medical_field"] == "gastroenterology"
    assert payload["active"]["is_active"] is True
    assert payload["counts"]["unit"] == 1
    assert terminology_routes.active_terminology_selection() == (
        "published_terminology",
        "2026.04.30",
    )


def test_active_selection_rejects_stale_registry_revision(
    tmp_path: Path,
) -> None:
    registry_path = _write_registry(tmp_path)
    stale_revision = terminology_routes._registry_revision(registry_path)

    current_revision = terminology_routes._set_active_selection(
        registry_path=registry_path,
        module_name="published_terminology",
        version="2026.04.30",
        expected_revision=stale_revision,
    )

    assert current_revision != stale_revision
    with pytest.raises(HttpError) as exc_info:
        terminology_routes._set_active_selection(
            registry_path=registry_path,
            module_name="published_terminology",
            version="2026.04.30",
            expected_revision=stale_revision,
        )
    assert getattr(exc_info.value, "status_code", None) == 409
    assert terminology_routes._registry_revision(registry_path) == current_revision


def test_concurrent_active_selections_have_one_compare_and_swap_winner(
    tmp_path: Path,
) -> None:
    registry_path = _write_registry(tmp_path)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    versions = registry["modules"]["published_terminology"]
    versions["2026.05.01"] = versions["2026.04.30"]
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    expected_revision = terminology_routes._registry_revision(registry_path)
    barrier = Barrier(2)

    def select(version: str) -> tuple[str, str | int]:
        barrier.wait()
        try:
            revision = terminology_routes._set_active_selection(
                registry_path=registry_path,
                module_name="published_terminology",
                version=version,
                expected_revision=expected_revision,
            )
            return "selected", revision
        except HttpError as exc:
            return "conflict", int(getattr(exc, "status_code", 0))

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(select, ["2026.04.30", "2026.05.01"]))

    assert sorted(status for status, _ in outcomes) == ["conflict", "selected"]
    assert next(value for status, value in outcomes if status == "conflict") == 409
    assert terminology_routes._active_selection_from_registry(registry_path) in {
        ("published_terminology", "2026.04.30"),
        ("published_terminology", "2026.05.01"),
    }


def test_export_active_terminology_bundle_as_fhir(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    registry_path = _write_registry(tmp_path, active=True)
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))

    response = Client().get("/base_api/terminology/active/fhir", secure=True)

    assert response.status_code == 200
    payload = response.json()
    extension = {
        "url": "https://wg-lux.de/fhir/StructureDefinition/lx-medical-field",
        "valueCode": "gastroenterology",
    }
    assert payload["resourceType"] == "Bundle"
    assert extension in payload["extension"]
    unit_code_system = next(
        entry["resource"]
        for entry in payload["entry"]
        if entry["resource"]["id"] == "lx-unit-cs"
    )
    assert extension in unit_code_system["extension"]
    assert unit_code_system["concept"][0]["code"] == "published-unit"
    assert unit_code_system["concept"][0]["display"] == "published_unit"
    assert {
        "code": "unit-abbreviation",
        "valueString": "u",
    } in unit_code_system["concept"][0]["property"]


def test_export_registered_terminology_bundle_as_fhir_without_selecting(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    registry_path = _write_registry(tmp_path)
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))

    response = Client().get(
        "/base_api/terminology/bundles/published_terminology/2026.04.30/fhir",
        secure=True,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["resourceType"] == "Bundle"
    assert payload["extension"][0]["valueCode"] == "gastroenterology"


def test_import_terminology_bundle_zip_registers_without_changing_active_selection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "kb_registry.json"
    import_root = tmp_path / "imported-packages"
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))
    monkeypatch.setenv("LX_DTYPES_TERMINOLOGY_IMPORT_ROOT", str(import_root))

    response = Client().post(
        "/base_api/terminology/bundles/import",
        data={
            "file": SimpleUploadedFile(
                "published_terminology.zip",
                _editor_bundle_zip(),
                content_type="application/zip",
            )
        },
        secure=True,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["imported"]["module_name"] == "published_terminology"
    assert payload["imported"]["version"] == "2026.05.04"
    assert payload["imported"]["medical_field"] == "gastroenterology"
    assert payload["imported"]["is_active"] is False
    assert payload["revision"] == terminology_routes._registry_revision(registry_path)
    assert payload["counts"]["unit"] == 1
    assert terminology_routes.active_terminology_selection() is None

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    entry = registry["modules"]["published_terminology"]["2026.05.04"]
    assert "active" not in registry
    assert entry["medical_field"] == "gastroenterology"
    assert entry["sources"] == [
        {
            "kind": "filesystem",
            "input_dirs": [
                str((import_root / "published_terminology" / "2026.05.04").resolve())
            ],
        }
    ]
    assert (
        import_root
        / "published_terminology"
        / "2026.05.04"
        / "published_terminology"
        / "config.yaml"
    ).exists()


def test_import_rejects_overwriting_an_existing_bundle_version(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "kb_registry.json"
    import_root = tmp_path / "imported-packages"
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))
    monkeypatch.setenv("LX_DTYPES_TERMINOLOGY_IMPORT_ROOT", str(import_root))
    upload = SimpleUploadedFile(
        "published_terminology.zip",
        _editor_bundle_zip(),
        content_type="application/zip",
    )
    first_response = Client().post(
        "/base_api/terminology/bundles/import",
        data={"file": upload},
        secure=True,
    )
    original_registry = registry_path.read_bytes()

    second_response = Client().post(
        "/base_api/terminology/bundles/import",
        data={
            "file": SimpleUploadedFile(
                "published_terminology.zip",
                _editor_bundle_zip(),
                content_type="application/zip",
            )
        },
        secure=True,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409
    assert registry_path.read_bytes() == original_registry
    assert not list(registry_path.parent.glob(".*.tmp"))


def test_import_rejects_registered_identity_before_filesystem_publication(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "kb_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "modules": {
                    "published_terminology": {
                        "2026.05.04": {
                            "sources": [
                                {
                                    "kind": "filesystem",
                                    "input_dirs": ["/governed/existing/source"],
                                }
                            ]
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    import_root = tmp_path / "imported-packages"
    monkeypatch.setenv("LX_DTYPES_TERMINOLOGY_IMPORT_ROOT", str(import_root))
    original_registry = registry_path.read_bytes()

    with pytest.raises(HttpError) as exc_info:
        terminology_routes._install_terminology_zip(
            upload=cast(
                UploadedFile,
                SimpleUploadedFile(
                    "published_terminology.zip",
                    _editor_bundle_zip(),
                    content_type="application/zip",
                ),
            ),
            registry_path=registry_path,
        )

    assert getattr(exc_info.value, "status_code", None) == 409
    assert registry_path.read_bytes() == original_registry
    assert not import_root.exists()


def test_import_rejects_data_dir_path_traversal_before_host_system_parsing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "kb_registry.json"
    import_root = tmp_path / "imported-packages"
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))
    monkeypatch.setenv("LX_DTYPES_TERMINOLOGY_IMPORT_ROOT", str(import_root))

    response = Client().post(
        "/base_api/terminology/bundles/import",
        data={
            "file": SimpleUploadedFile(
                "published_terminology.zip",
                _bundle_zip_with_traversal_data_dir(),
                content_type="application/zip",
            )
        },
        secure=True,
    )

    assert response.status_code == 409
    assert b"could not be loaded after import" in response.content
    assert not (import_root / "published_terminology" / "2026.05.04").exists()


def test_import_validates_all_transitive_dependencies_before_registration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "kb_registry.json"
    import_root = tmp_path / "imported-packages"
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))
    monkeypatch.setenv("LX_DTYPES_TERMINOLOGY_IMPORT_ROOT", str(import_root))

    response = Client().post(
        "/base_api/terminology/bundles/import",
        data={
            "file": SimpleUploadedFile(
                "incomplete_bundle.zip",
                _bundle_zip_with_missing_transitive_dependency(),
                content_type="application/zip",
            )
        },
        secure=True,
    )

    assert response.status_code == 409
    assert b"missing_dependency" in response.content
    assert not registry_path.exists()
    assert not (import_root / "incomplete_bundle" / "1.0.0").exists()


def test_missing_registry_error_does_not_expose_server_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "private" / "registry.json"
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))

    response = Client().get("/base_api/terminology/bundles", secure=True)

    assert response.status_code == 404
    assert str(registry_path) not in response.content.decode()


def test_export_active_terminology_fhir_rejects_missing_active_selection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    registry_path = _write_registry(tmp_path)
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))

    response = Client().get("/base_api/terminology/active/fhir", secure=True)

    assert response.status_code == 404
    assert b"No active terminology bundle is selected" in response.content


def test_select_terminology_bundle_rejects_unregistered_version(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    registry_path = _write_registry(tmp_path)
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))

    response = Client().post(
        "/base_api/terminology/bundles/select",
        data=json.dumps(
            {
                "module_name": "published_terminology",
                "version": "missing",
                "expected_revision": terminology_routes._registry_revision(
                    registry_path
                ),
            }
        ),
        content_type="application/json",
        secure=True,
    )

    assert response.status_code == 404


def test_validate_imported_bundle_uses_resolved_version(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, str | None] = {}

    monkeypatch.setattr(
        terminology_routes,
        "get_knowledge_base_identity",
        lambda module_name, *, version=None, input_dirs=None: (
            module_name,
            "2026.05.04",
        ),
    )

    def _fake_load_knowledge_base(
        module_name: str,
        *,
        version: str | None = None,
        input_dirs: list[Path] | None = None,
    ) -> object:
        del input_dirs
        captured["module_name"] = module_name
        captured["version"] = version

        class _Kb:
            def export_core_concepts(self) -> dict[str, list[dict[str, str]]]:
                return {"unit": [{"name": "demo"}]}

        return _Kb()

    monkeypatch.setattr(
        terminology_routes,
        "load_knowledge_base",
        _fake_load_knowledge_base,
    )

    counts = terminology_routes._validate_imported_bundle(
        module_name="published_terminology",
        input_dir=tmp_path,
    )

    assert counts == {"unit": 1}
    assert captured == {
        "module_name": "published_terminology",
        "version": "2026.05.04",
    }


def test_terminology_import_root_uses_env_or_registry_parent(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "kb_registry.json"
    registry_path.write_text("{}")
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))

    assert terminology_routes._terminology_import_root(registry_path) == (
        (registry_path.parent / "terminology-packages").resolve()
    )

    import_root = tmp_path / "configured-import-root"
    monkeypatch.setenv(
        "LX_DTYPES_TERMINOLOGY_IMPORT_ROOT",
        str(import_root),
    )
    assert (
        terminology_routes._terminology_import_root(registry_path)
        == import_root.resolve()
    )
