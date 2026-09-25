# ruff: noqa: FLY002 - line lists keep embedded YAML fixtures readable
"""Terminology API contracts against a per-test central resolver.

No application ``main`` import: each HTTP fixture registers fresh routes against
its configured service. No test hydrates shipped data or uses user-data storage.
"""

from __future__ import annotations

import json
import sys
import zipfile
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from threading import Barrier
from types import ModuleType
from typing import IO, Any
from uuid import uuid4

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import clear_url_caches, path
from ninja import NinjaAPI
from pytest_django.fixtures import SettingsWrapper

from lx_dtypes.django.api import terminology_routes
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.interface.KnowledgeBaseResolver import (
    clear_knowledge_base_resolver_caches,
)
from lx_dtypes.terminology import terminology_loader as central
from lx_dtypes.terminology import terminology_service as service_module
from lx_dtypes.terminology.lookup_tracker import consume_runtime_lookup_trackers
from lx_dtypes.terminology.terminology_service import (
    TerminologyError,
    TerminologyService,
)


@pytest.fixture(autouse=True)
def isolated_terminology(
    settings: SettingsWrapper,
    tmp_path: Path,
) -> Iterator[None]:
    """Isolate configuration and caches before a service or API is constructed."""
    settings.TERMINOLOGY_ROOT = tmp_path / "terminology"
    central.get_terminology_service.cache_clear()
    clear_knowledge_base_resolver_caches()
    consume_runtime_lookup_trackers()
    try:
        yield
    finally:
        consume_runtime_lookup_trackers()
        clear_knowledge_base_resolver_caches()
        central.get_terminology_service.cache_clear()


@pytest.fixture
def terminology_service() -> TerminologyService:
    return central.get_terminology_service()


@dataclass
class TerminologyApi:
    client: Client
    service: TerminologyService
    actor: object | None = field(default_factory=object)
    write_allowed: bool = True
    cache_clears: list[None] = field(default_factory=list)
    tracked: list[KnowledgeBase] = field(default_factory=list)


@pytest.fixture
def terminology_api(
    terminology_service: TerminologyService,
    settings: SettingsWrapper,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TerminologyApi]:
    """Exercise real Django/Ninja HTTP handling without host application routes."""
    harness = TerminologyApi(client=Client(), service=terminology_service)
    monkeypatch.setattr(
        terminology_routes, "register_runtime_lookup_tracker", harness.tracked.append
    )
    # Authentication is an explicit test policy, not an accidental open-write default.
    api = NinjaAPI(
        urls_namespace=f"terminology-tests-{uuid4().hex}",
        docs_url=None,
        openapi_url=None,
    )
    terminology_routes.register_terminology_routes(
        api,
        service=terminology_service,
        clear_kb_caches=lambda: harness.cache_clears.append(None),
        authenticate_request_user=lambda request: harness.actor,
        terminology_write_access_allowed=lambda actor: harness.write_allowed,
    )
    module_name = f"_terminology_test_urls_{uuid4().hex}"
    urlconf = ModuleType(module_name)
    monkeypatch.setattr(
        urlconf, "urlpatterns", [path("base_api/", api.urls)], raising=False
    )
    monkeypatch.setitem(sys.modules, module_name, urlconf)
    settings.ROOT_URLCONF = module_name
    # Middleware/host-RBAC integration has its own tests; this file tests the adapter.
    settings.MIDDLEWARE = []
    settings.ALLOWED_HOSTS = ["testserver"]
    clear_url_caches()
    try:
        yield harness
    finally:
        clear_url_caches()


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


def _write_registry(
    root: Path,
    *,
    active: bool = False,
    versions: tuple[str, ...] = ("2026.04.30",),
) -> Path:
    """Each registered version has its own matching config and filesystem root."""
    entries: dict[str, object] = {}
    for version in versions:
        kb_root = root / "knowledge-bases" / version
        bundle_dir = kb_root / "published_terminology"
        _write_module_config(
            bundle_dir,
            name="published_terminology",
            version=version,
            medical_field="gastroenterology",
            modules=["lx_units"],
            data_dirs=[],
        )
        units_dir = bundle_dir / "lx_units"
        _write_module_config(
            units_dir,
            name="lx_units",
            version=version,
            data_dirs=["./data"],
        )
        _write_unit(units_dir, name="published_unit")
        entries[version] = {
            "sources": [{"kind": "filesystem", "input_dirs": [str(kb_root)]}]
        }
    root.mkdir(parents=True, exist_ok=True)
    registry_path = root / "registry.json"
    payload: dict[str, object] = {
        "modules": {"published_terminology": entries},
    }
    if active:
        payload["active"] = {
            "module_name": "published_terminology",
            "version": versions[0],
        }
    registry_path.write_text(json.dumps(payload), encoding="utf-8")
    return registry_path


def _registry_revision(registry_path: Path) -> str:
    """Independent byte-level assertion, not a call to a retired route helper."""
    return f"sha256:{sha256(registry_path.read_bytes()).hexdigest()}"


def _upload(content: bytes | None = None) -> SimpleUploadedFile:
    return SimpleUploadedFile(
        "terminology.zip",
        _editor_bundle_zip() if content is None else content,
        content_type="application/zip",
    )


def _assert_import_storage_empty(service: TerminologyService) -> None:
    # Creating the empty parent is allowed; publishing or leaking staged data is not.
    assert not service.import_root.exists() or not list(service.import_root.iterdir())


def test_service_construction_does_not_create_or_hydrate_storage(
    terminology_service: TerminologyService,
    tmp_path: Path,
) -> None:
    assert terminology_service.registry_path == (
        tmp_path / "terminology" / "registry.json"
    )
    assert central.get_terminology_service() is terminology_service
    assert not terminology_service.registry_path.parent.exists()


def test_list_terminology_bundles_reports_no_active_selection(
    terminology_api: TerminologyApi,
) -> None:
    registry_path = _write_registry(terminology_api.service.registry_path.parent)
    response = terminology_api.client.get("/base_api/terminology/bundles", secure=True)

    assert response.status_code == 200
    payload = response.json()
    assert payload["revision"] == _registry_revision(registry_path)
    assert payload["active"] is None
    assert payload["bundles"] == [
        {
            "module_name": "published_terminology",
            "version": "2026.04.30",
            "medical_field": "gastroenterology",
            "is_active": False,
        }
    ]
    assert terminology_api.service.active_identity() is None
    with pytest.raises(TerminologyError) as error:
        central.active_kb_identity()
    assert error.value.status == 409


def test_list_terminology_bundles_does_not_expose_storage_source(
    terminology_api: TerminologyApi,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_url = (
        "https://github.com/wg-lux/lx-data-models/tree/main/demo-data/star_upper_gi"
    )
    registry_path = terminology_api.service.registry_path
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        json.dumps(
            {
                "modules": {
                    "star_upper_gi": {
                        "0.1.1": {
                            "sources": [
                                {"kind": "filesystem", "input_dirs": [source_url]}
                            ],
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    def unexpected_remote_load(*args: object, **kwargs: object) -> Path:
        pytest.fail("Listing bundle metadata must not download remote resources")

    monkeypatch.setattr(
        service_module, "resolve_remote_data_root", unexpected_remote_load
    )
    response = terminology_api.client.get("/base_api/terminology/bundles", secure=True)

    assert response.status_code == 200
    bundle = response.json()["bundles"][0]
    assert set(bundle) == {"module_name", "version", "medical_field", "is_active"}
    assert source_url.encode() not in response.content
    assert str(registry_path).encode() not in response.content


def test_select_terminology_bundle_sets_active_runtime_selection(
    terminology_api: TerminologyApi,
) -> None:
    registry_path = _write_registry(terminology_api.service.registry_path.parent)
    response = terminology_api.client.post(
        "/base_api/terminology/bundles/select",
        data=json.dumps(
            {
                "module_name": "published_terminology",
                "version": "2026.04.30",
                "expected_revision": _registry_revision(registry_path),
            }
        ),
        content_type="application/json",
        secure=True,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["revision"] == _registry_revision(registry_path)
    assert payload["active"] == {
        "module_name": "published_terminology",
        "version": "2026.04.30",
        "medical_field": "gastroenterology",
        "is_active": True,
    }
    assert payload["counts"]["unit"] == 1
    assert central.active_kb_identity() == ("published_terminology", "2026.04.30")
    kb = central.load_module_kb("published_terminology")
    assert kb.config is not None and kb.config.version == "2026.04.30"
    assert len(terminology_api.tracked) == 1
    assert len(terminology_api.cache_clears) == 1


def test_active_selection_rejects_stale_registry_revision(
    terminology_service: TerminologyService,
) -> None:
    registry_path = _write_registry(terminology_service.registry_path.parent)
    stale_revision = _registry_revision(registry_path)
    selected: list[KnowledgeBase] = []
    cleared: list[None] = []
    result = terminology_service.select(
        "published_terminology",
        "2026.04.30",
        expected_revision=stale_revision,
        on_selected=selected.append,
        clear_application_caches=lambda: cleared.append(None),
    )
    current_bytes = registry_path.read_bytes()

    assert result.revision != stale_revision
    with pytest.raises(TerminologyError) as error:
        terminology_service.select(
            "published_terminology",
            "2026.04.30",
            expected_revision=stale_revision,
            on_selected=selected.append,
            clear_application_caches=lambda: cleared.append(None),
        )
    assert error.value.status == 409
    assert registry_path.read_bytes() == current_bytes
    assert _registry_revision(registry_path) == result.revision
    assert len(selected) == len(cleared) == 1


def test_concurrent_active_selections_have_one_compare_and_swap_winner(
    terminology_service: TerminologyService,
) -> None:
    versions = ("2026.04.30", "2026.05.01")
    registry_path = _write_registry(
        terminology_service.registry_path.parent,
        versions=versions,
    )
    # Both contenders must be loadable; a wrong-version artifact is not a CAS test.
    for version in versions:
        kb = terminology_service.load("published_terminology", version)
        assert kb.config is not None and kb.config.version == version
    expected_revision = _registry_revision(registry_path)
    barrier = Barrier(2)
    selected: list[KnowledgeBase] = []
    cleared: list[None] = []

    def select(version: str) -> tuple[str, str | int]:
        barrier.wait(timeout=10)
        try:
            result = terminology_service.select(
                "published_terminology",
                version,
                expected_revision=expected_revision,
                on_selected=selected.append,
                clear_application_caches=lambda: cleared.append(None),
            )
            return "selected", result.revision
        except TerminologyError as exc:
            return "conflict", exc.status

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(select, versions))

    assert sorted(status for status, _ in outcomes) == ["conflict", "selected"]
    assert next(value for status, value in outcomes if status == "conflict") == 409
    assert next(value for status, value in outcomes if status == "selected") == (
        _registry_revision(registry_path)
    )
    assert terminology_service.active_identity() in {
        ("published_terminology", version) for version in versions
    }
    assert len(selected) == len(cleared) == 1


def test_export_active_terminology_bundle_as_fhir(
    terminology_api: TerminologyApi,
) -> None:
    _write_registry(terminology_api.service.registry_path.parent, active=True)
    response = terminology_api.client.get(
        "/base_api/terminology/active/fhir", secure=True
    )

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
    assert {"code": "unit-abbreviation", "valueString": "u"} in (
        unit_code_system["concept"][0]["property"]
    )


def test_export_registered_terminology_bundle_as_fhir_without_selecting(
    terminology_api: TerminologyApi,
) -> None:
    _write_registry(terminology_api.service.registry_path.parent)
    response = terminology_api.client.get(
        "/base_api/terminology/bundles/published_terminology/2026.04.30/fhir",
        secure=True,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["resourceType"] == "Bundle"
    assert payload["extension"][0]["valueCode"] == "gastroenterology"
    assert terminology_api.service.active_identity() is None


def test_import_terminology_bundle_zip_registers_without_changing_active_selection(
    terminology_api: TerminologyApi,
) -> None:
    service = terminology_api.service
    response = terminology_api.client.post(
        "/base_api/terminology/bundles/import",
        data={"file": _upload()},
        secure=True,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["imported"] == {
        "module_name": "published_terminology",
        "version": "2026.05.04",
        "medical_field": "gastroenterology",
        "is_active": False,
    }
    assert payload["revision"] == _registry_revision(service.registry_path)
    assert payload["counts"]["unit"] == 1
    assert service.active_identity() is None
    assert not terminology_api.tracked
    assert len(terminology_api.cache_clears) == 1

    registry = json.loads(service.registry_path.read_text(encoding="utf-8"))
    entry = registry["modules"]["published_terminology"]["2026.05.04"]
    assert "active" not in registry
    assert entry["medical_field"] == "gastroenterology"
    assert len(entry["sources"]) == 1
    source = entry["sources"][0]
    assert source["kind"] == "filesystem"
    assert len(source["input_dirs"]) == 1
    input_root = Path(source["input_dirs"][0])
    assert input_root.is_absolute()
    assert input_root.parent == service.import_root
    assert not input_root.name.startswith(".")
    assert (input_root / "published_terminology" / "config.yaml").is_file()
    kb = central.load_module_kb("published_terminology", version="2026.05.04")
    assert kb.config is not None
    assert kb.config.source_file is not None
    assert Path(kb.config.source_file).parent == input_root / "published_terminology"


def test_import_preserves_an_existing_active_identity(
    terminology_api: TerminologyApi,
) -> None:
    _write_registry(terminology_api.service.registry_path.parent, active=True)
    response = terminology_api.client.post(
        "/base_api/terminology/bundles/import",
        data={"file": _upload()},
        secure=True,
    )
    assert response.status_code == 200
    assert central.active_kb_identity() == ("published_terminology", "2026.04.30")
    assert response.json()["imported"]["is_active"] is False


def test_import_rejects_overwriting_an_existing_bundle_version(
    terminology_api: TerminologyApi,
) -> None:
    service = terminology_api.service
    first_response = terminology_api.client.post(
        "/base_api/terminology/bundles/import",
        data={"file": _upload()},
        secure=True,
    )
    assert first_response.status_code == 200
    original_registry = service.registry_path.read_bytes()
    original_files = {
        path.relative_to(service.import_root): path.read_bytes()
        for path in service.import_root.rglob("*")
        if path.is_file()
    }

    second_response = terminology_api.client.post(
        "/base_api/terminology/bundles/import",
        data={"file": _upload()},
        secure=True,
    )
    assert second_response.status_code == 409
    assert service.registry_path.read_bytes() == original_registry
    assert {
        path.relative_to(service.import_root): path.read_bytes()
        for path in service.import_root.rglob("*")
        if path.is_file()
    } == original_files
    assert not list(service.import_root.glob(".staging-*"))
    assert len(terminology_api.cache_clears) == 1


def test_import_rejects_registered_identity_before_filesystem_publication(
    terminology_service: TerminologyService,
) -> None:
    registry_path = terminology_service.registry_path
    registry_path.parent.mkdir(parents=True)
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
                        },
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    original_registry = registry_path.read_bytes()

    with pytest.raises(TerminologyError) as error:
        terminology_service.import_zip(BytesIO(_editor_bundle_zip()))

    assert error.value.status == 409
    assert registry_path.read_bytes() == original_registry
    _assert_import_storage_empty(terminology_service)


def test_import_rejects_data_dir_path_traversal_before_host_system_parsing(
    terminology_api: TerminologyApi,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = terminology_api.service
    # From <root>/terminology-packages/.staging-*/<module>, ../../../etc
    # points to <root>/etc. Supply a real outside file and prohibit opening it.
    outside = service.registry_path.parent / "etc"
    outside.mkdir(parents=True)
    forbidden = outside / "host.yaml"
    forbidden.write_text(
        "- model: unit\n  name: host_secret\n  abbreviation: s\n", encoding="utf-8"
    )
    original_open = Path.open

    def guarded_open(path: Path, *args: Any, **kwargs: Any) -> IO[Any]:
        if path.resolve() == forbidden.resolve():
            pytest.fail("Import attempted to read outside its staged bundle")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    response = terminology_api.client.post(
        "/base_api/terminology/bundles/import",
        data={"file": _upload(_bundle_zip_with_traversal_data_dir())},
        secure=True,
    )

    assert response.status_code == 409
    assert b"could not be loaded" in response.content
    assert str(outside).encode() not in response.content
    assert not service.registry_path.exists()
    _assert_import_storage_empty(service)


def test_import_validates_all_transitive_dependencies_before_registration(
    terminology_api: TerminologyApi,
) -> None:
    response = terminology_api.client.post(
        "/base_api/terminology/bundles/import",
        data={"file": _upload(_bundle_zip_with_missing_transitive_dependency())},
        secure=True,
    )
    assert response.status_code == 409
    # Internal loader details live in the exception cause, not the HTTP response.
    assert b"could not be loaded" in response.content
    assert not terminology_api.service.registry_path.exists()
    assert not terminology_api.cache_clears
    _assert_import_storage_empty(terminology_api.service)


def test_missing_dependency_cause_is_preserved(
    terminology_service: TerminologyService,
) -> None:
    with pytest.raises(TerminologyError) as error:
        terminology_service.import_zip(
            BytesIO(_bundle_zip_with_missing_transitive_dependency())
        )
    assert error.value.status == 409
    cause = error.value.__cause__
    assert cause is not None
    assert "missing_dependency" in str(cause)
    assert not terminology_service.registry_path.exists()
    _assert_import_storage_empty(terminology_service)


def test_missing_registry_error_does_not_expose_server_path(
    terminology_api: TerminologyApi,
) -> None:
    response = terminology_api.client.get("/base_api/terminology/bundles", secure=True)
    assert response.status_code == 404
    assert str(terminology_api.service.registry_path).encode() not in response.content
    assert not terminology_api.service.registry_path.parent.exists()


def test_export_active_terminology_fhir_rejects_missing_active_selection(
    terminology_api: TerminologyApi,
) -> None:
    _write_registry(terminology_api.service.registry_path.parent)
    response = terminology_api.client.get(
        "/base_api/terminology/active/fhir", secure=True
    )
    assert response.status_code == 404
    assert b"No active terminology bundle is selected" in response.content


def test_select_terminology_bundle_rejects_unregistered_version(
    terminology_api: TerminologyApi,
) -> None:
    registry_path = _write_registry(terminology_api.service.registry_path.parent)
    before = registry_path.read_bytes()
    response = terminology_api.client.post(
        "/base_api/terminology/bundles/select",
        data=json.dumps(
            {
                "module_name": "published_terminology",
                "version": "missing",
                "expected_revision": _registry_revision(registry_path),
            }
        ),
        content_type="application/json",
        secure=True,
    )
    assert response.status_code == 404
    assert registry_path.read_bytes() == before
    assert not terminology_api.tracked
    assert not terminology_api.cache_clears


def test_import_passes_declared_version_and_explicit_paths_to_loader(
    terminology_service: TerminologyService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[tuple[str, str | None, tuple[Path, ...]]] = []
    real_load = service_module.load_knowledge_base

    def recording_load(
        module_name: str,
        *,
        version: str | None = None,
        input_dirs: list[Path] | None = None,
    ) -> KnowledgeBase:
        assert input_dirs
        captured.append((module_name, version, tuple(input_dirs)))
        return real_load(module_name, version=version, input_dirs=input_dirs)

    monkeypatch.setattr(service_module, "load_knowledge_base", recording_load)
    result = terminology_service.import_zip(BytesIO(_editor_bundle_zip()))
    assert result.counts["unit"] == 1
    # Validate both staging and the final published location, not just a mocked KB.
    assert len(captured) >= 2
    for module_name, version, paths in captured:
        assert (module_name, version) == ("published_terminology", "2026.05.04")
        assert len(paths) == 1 and paths[0].is_absolute()
        assert paths[0].parent == terminology_service.import_root
    assert captured[0][2] != captured[-1][2]
    assert captured[-1][2][0].is_dir()
    assert not captured[0][2][0].exists()


def test_terminology_import_root_is_derived_from_registry_parent(
    terminology_service: TerminologyService,
) -> None:
    assert terminology_service.import_root == (
        terminology_service.registry_path.parent / "terminology-packages"
    )
    assert not terminology_service.import_root.exists()


def test_retired_environment_variables_do_not_redirect_the_central_service(
    terminology_api: TerminologyApi,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Negative compatibility test: old environment values must have no effect."""
    ignored_registry = tmp_path / "ignored" / "old-registry.json"
    ignored_imports = tmp_path / "ignored-imports"
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(ignored_registry))
    monkeypatch.setenv("LX_DTYPES_TERMINOLOGY_IMPORT_ROOT", str(ignored_imports))
    response = terminology_api.client.post(
        "/base_api/terminology/bundles/import",
        data={"file": _upload()},
        secure=True,
    )
    assert response.status_code == 200
    assert terminology_api.service.registry_path.exists()
    assert terminology_api.service.import_root.is_dir()
    assert not ignored_registry.parent.exists()
    assert not ignored_imports.exists()
    kb = central.load_module_kb("published_terminology", version="2026.05.04")
    assert kb.config is not None and kb.config.version == "2026.05.04"


@pytest.mark.parametrize("operation", ["import", "select"])
@pytest.mark.parametrize("anonymous", [True, False])
def test_terminology_writes_require_authorization(
    terminology_api: TerminologyApi,
    operation: str,
    anonymous: bool,
) -> None:
    terminology_api.actor = None if anonymous else object()
    terminology_api.write_allowed = False
    if operation == "import":
        response = terminology_api.client.post(
            "/base_api/terminology/bundles/import",
            data={"file": _upload()},
            secure=True,
        )
    else:
        response = terminology_api.client.post(
            "/base_api/terminology/bundles/select",
            data=json.dumps(
                {
                    "module_name": "published_terminology",
                    "version": "2026.04.30",
                    "expected_revision": f"sha256:{'0' * 64}",
                }
            ),
            content_type="application/json",
            secure=True,
        )
    assert response.status_code == (401 if anonymous else 403)
    assert not terminology_api.service.registry_path.exists()
    assert not terminology_api.service.import_root.exists()
    assert not terminology_api.tracked
    assert not terminology_api.cache_clears


def test_central_resolver_reads_selection_changes_from_another_service(
    terminology_service: TerminologyService,
) -> None:
    registry_path = _write_registry(
        terminology_service.registry_path.parent,
        active=True,
        versions=("2026.04.30", "2026.05.01"),
    )
    assert central.active_kb_identity() == ("published_terminology", "2026.04.30")
    writer = TerminologyService(registry_path=registry_path)
    writer.select(
        "published_terminology",
        "2026.05.01",
        expected_revision=_registry_revision(registry_path),
        on_selected=lambda kb: None,
        clear_application_caches=lambda: None,
    )
    # Reuse the cached central service; its active identity must not be cached.
    assert central.get_terminology_service() is terminology_service
    assert central.active_kb_identity() == ("published_terminology", "2026.05.01")
    active = central.load_module_kb("published_terminology")
    historical = central.load_module_kb("published_terminology", version="2026.04.30")
    assert active.config is not None and active.config.version == "2026.05.01"
    assert historical.config is not None and historical.config.version == "2026.04.30"


def test_registry_identity_must_match_its_artifact(
    terminology_service: TerminologyService,
) -> None:
    registry_path = _write_registry(terminology_service.registry_path.parent)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    versions = registry["modules"]["published_terminology"]
    versions["2026.05.01"] = versions["2026.04.30"]
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    with pytest.raises(TerminologyError) as error:
        central.load_module_kb("published_terminology", version="2026.05.01")
    assert error.value.status == 409
    assert terminology_service.active_identity() is None
