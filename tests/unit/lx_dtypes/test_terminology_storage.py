"""Caller-owned registry and package locations must remain isolated."""

import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
import yaml

from lx_dtypes.models.interface.KnowledgeBaseResolver import (
    clear_knowledge_base_resolver_caches,
)
from lx_dtypes.scripts.kb_registry import main
from lx_dtypes.terminology import terminology_loader as loader
from lx_dtypes.terminology.terminology_service import (
    TerminologyError,
    TerminologyService,
)
from lx_dtypes.utils.deployment_setup import parse_deployment_setup, resolve_deployment
from tests.paths import PACKAGE_ROOT


@pytest.fixture
def package(tmp_path: Path) -> Path:
    source = PACKAGE_ROOT.parent / "docs/examples/dtypes_packages/training_preset"
    target = tmp_path / "caller packages" / "training_preset"
    shutil.copytree(source, target)
    return target


@pytest.fixture(autouse=True)
def isolated_caches():
    clear_knowledge_base_resolver_caches()
    yield
    clear_knowledge_base_resolver_caches()


def test_registration_preserves_source_and_does_not_provision_or_activate(
    package: Path, tmp_path: Path
) -> None:
    service = TerminologyService(
        registry_path=tmp_path / "separate registry" / "registry.json"
    )
    before = {
        p.relative_to(package): p.read_bytes()
        for p in package.rglob("*")
        if p.is_file()
    }
    bundle = service.register_local("training_preset", "1.0.0", input_dirs=[package])
    assert bundle.module_name == "training_preset"
    assert not bundle.is_active
    assert service.active_identity() is None
    assert not service.import_root.exists()
    assert not (service.registry_path.parent / "shipped").exists()
    assert before == {
        p.relative_to(package): p.read_bytes()
        for p in package.rglob("*")
        if p.is_file()
    }
    assert "training_setup" in service.load("training_preset", "1.0.0").study_preset
    assert service.source_paths("training_preset", "1.0.0") == [package]
    original = service.registry_path.read_bytes()
    service.register_local("training_preset", "1.0.0", input_dirs=[package, package])
    assert service.registry_path.read_bytes() == original


def test_registration_conflict_preserves_registry(
    package: Path, tmp_path: Path
) -> None:
    service = TerminologyService(registry_path=tmp_path / "registry.json")
    service.register_local("training_preset", "1.0.0", input_dirs=[package])
    other = tmp_path / "other" / "training_preset"
    shutil.copytree(package, other)
    before = service.registry_path.read_bytes()
    with pytest.raises(TerminologyError, match="already registered"):
        service.register_local("training_preset", "1.0.0", input_dirs=[other])
    assert before == service.registry_path.read_bytes()


def test_dependency_can_live_in_another_explicit_source_root(
    package: Path, tmp_path: Path
) -> None:
    dependency = tmp_path / "shared release" / "shared_terms"
    dependency.mkdir(parents=True)
    (dependency / "config.yaml").write_text(
        "name: shared_terms\nversion: '1.0.0'\ndata:\n  files: [types.yml]\n"
    )
    (dependency / "types.yml").write_text(
        "- model: examination_type\n  name: shared_type\n"
    )
    manifest = package / "config.yaml"
    payload = yaml.safe_load(manifest.read_text())
    payload["depends_on"] = ["shared_terms"]
    manifest.write_text(yaml.safe_dump(payload))
    service = TerminologyService(tmp_path / "registry.json")
    service.register_local("training_preset", "1.0.0", input_dirs=[package, dependency])
    assert "shared_type" in service.load("training_preset", "1.0.0").examination_type
    assert service.source_paths("training_preset", "1.0.0") == [package, dependency]


@pytest.mark.parametrize(
    "kind",
    ["empty", "relative", "missing", "file", "wrong_version", "missing_dependency"],
)
def test_invalid_registration_does_not_create_registry(
    package: Path, tmp_path: Path, kind: str
) -> None:
    service = TerminologyService(registry_path=tmp_path / "registry.json")
    paths = [package]
    version = "1.0.0"
    if kind == "empty":
        paths = []
    elif kind == "relative":
        paths = [Path("relative")]
    elif kind == "missing":
        paths = [tmp_path / "missing"]
    elif kind == "file":
        paths = [package / "config.yaml"]
    elif kind == "wrong_version":
        version = "2.0.0"
    else:
        manifest = package / "config.yaml"
        payload = yaml.safe_load(manifest.read_text())
        payload["depends_on"] = ["missing_dependency"]
        manifest.write_text(yaml.safe_dump(payload))
    with pytest.raises(TerminologyError):
        service.register_local("training_preset", version, input_dirs=paths)
    assert not service.registry_path.exists()


def test_explicit_services_isolate_same_identity_from_host_and_environment(
    package: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = TerminologyService(registry_path=tmp_path / "centre_a" / "registry.json")
    second = TerminologyService(registry_path=tmp_path / "centre_b" / "registry.json")
    other = tmp_path / "second source" / "training_preset"
    shutil.copytree(package, other)
    manifest = other / "config.yaml"
    payload = yaml.safe_load(manifest.read_text())
    payload["description"] = "Second isolated authoring registry"
    manifest.write_text(yaml.safe_dump(payload))
    first.register_local("training_preset", "1.0.0", input_dirs=[package])
    second.register_local("training_preset", "1.0.0", input_dirs=[other])
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(tmp_path / "wrong.json"))
    monkeypatch.chdir(tmp_path)

    def forbidden_default() -> TerminologyService:
        raise AssertionError("Explicit service must not access the global host service")

    monkeypatch.setattr(loader, "get_terminology_service", forbidden_default)
    for service, source in [(first, package), (second, other)]:
        service.select(
            "training_preset",
            "1.0.0",
            expected_revision=service.list_bundles().revision,
            on_selected=lambda kb: None,
            clear_application_caches=lambda: None,
        )
        assert loader.active_kb_identity(service=service) == (
            "training_preset",
            "1.0.0",
        )
        assert (
            loader.load_module_kb("training_preset", service=service).config.source_file
            == source / "config.yaml"
        )
        assert (
            loader.resolve_module_path(
                "training_preset", version="1.0.0", for_write=True, service=service
            )
            == source
        )
    assert (
        loader.load_module_kb(
            "training_preset", version="1.0.0", service=second
        ).config.description
        == "Second isolated authoring registry"
    )
    with pytest.raises(TerminologyError, match="not registered"):
        loader.load_module_kb("absent", version="1.0.0", service=first)


def test_registration_revalidates_an_edited_source(
    package: Path, tmp_path: Path
) -> None:
    service = TerminologyService(registry_path=tmp_path / "registry.json")
    service.register_local("training_preset", "1.0.0", input_dirs=[package])
    before = service.registry_path.read_bytes()
    (package / "config.yaml").write_text("name: training_preset\nversion: '9.0.0'\n")
    with pytest.raises(TerminologyError):
        service.register_local("training_preset", "1.0.0", input_dirs=[package])
    assert before == service.registry_path.read_bytes()


def test_cached_package_does_not_hide_unavailable_storage(
    package: Path, tmp_path: Path
) -> None:
    service = TerminologyService(registry_path=tmp_path / "registry.json")
    service.register_local("training_preset", "1.0.0", input_dirs=[package])
    service.load("training_preset", "1.0.0")
    shutil.rmtree(package)
    with pytest.raises(TerminologyError, match="source directory is unavailable"):
        service.load("training_preset", "1.0.0")


def test_multicentre_document_has_portable_content_identity(
    package: Path, tmp_path: Path
) -> None:
    setup = parse_deployment_setup(
        (
            PACKAGE_ROOT.parent / "docs/examples/dtypes_packages/training_centre.yml"
        ).read_text()
    )
    other = tmp_path / "another centre" / "training_preset"
    shutil.copytree(package, other)
    first = TerminologyService(tmp_path / "centre_a" / "registry.json")
    second = TerminologyService(tmp_path / "centre_b" / "registry.json")
    first.register_local("training_preset", "1.0.0", input_dirs=[package])
    second.register_local("training_preset", "1.0.0", input_dirs=[other])
    first_lock = resolve_deployment(setup, first).lock
    second_lock = resolve_deployment(setup, second).lock
    assert first_lock.packages == second_lock.packages
    assert str(tmp_path) not in second_lock.model_dump_json()
    assert first.active_identity() is None and second.active_identity() is None
    # Reusing a version with changed bytes cannot preserve the reviewed digest.
    data = other / "data/examinations.yml"
    data.write_text(data.read_text() + "\n# Altered release content\n")
    assert resolve_deployment(setup, second).lock.packages != first_lock.packages


def test_concurrent_same_registration_is_idempotent(
    package: Path, tmp_path: Path
) -> None:
    service = TerminologyService(registry_path=tmp_path / "registry.json")
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(
            executor.map(
                lambda _: service.register_local(
                    "training_preset", "1.0.0", input_dirs=[package]
                ),
                range(2),
            )
        )
    assert all(result.module_name == "training_preset" for result in results)
    assert len(service.list_bundles().bundles) == 1


def test_cli_registration_and_failure(
    package: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    registry = tmp_path / "registry.json"
    args = [
        "register-local",
        str(registry),
        "--module",
        "training_preset",
        "--version",
        "1.0.0",
        "--input-dir",
        str(package),
    ]
    assert main(args) == 0
    assert json.loads(capsys.readouterr().out)["is_active"] is False
    before = registry.read_bytes()
    args[args.index("1.0.0")] = "9.0.0"
    assert main(args) == 1
    assert json.loads(capsys.readouterr().err)["status"] == "error"
    assert before == registry.read_bytes()
