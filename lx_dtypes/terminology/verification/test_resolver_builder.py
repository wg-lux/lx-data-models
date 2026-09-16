from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from lx_dtypes.django.api import report_template_builder as builder
from lx_dtypes.models.interface.data_roots import package_data_root
from lx_dtypes.models.interface.KnowledgeBaseResolver import (
    clear_knowledge_base_resolver_caches,
)
from lx_dtypes.terminology import terminology_loader as central
from lx_dtypes.terminology.terminology_service import TerminologyError


@pytest.mark.parametrize("value", [None, "", "relative", Path("relative")])
def test_invalid_roots_are_rejected(monkeypatch, value):
    monkeypatch.setattr(settings, "TERMINOLOGY_ROOT", value)
    central.get_terminology_service.cache_clear()
    with pytest.raises(ImproperlyConfigured):
        central.get_terminology_service()


def test_source_fallback_ignores_cwd(storage, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    kb = central.load_module_kb("star_upper_gi")
    assert kb.config.source_file.is_relative_to(storage)
    assert central.active_kb_identity() == ("star_upper_gi", "0.1.2")


def test_legacy_environment_variables_do_not_control_loading(storage, monkeypatch):
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", "/nonexistent/wrong.json")
    monkeypatch.setenv("LOOKUP_DTYPES_DATA_ROOT", "/nonexistent/wrong-data")
    assert central.load_module_kb("star_upper_gi").config.source_file.is_relative_to(
        storage
    )


def test_explicit_hydration_reads_current_setting_at_call_time(storage, monkeypatch):
    assert central.hydrate_shipped_terminology() == storage / "registry.json"
    assert (
        central.hydrate_shipped_terminology(str(storage)) == storage / "registry.json"
    )


def test_active_selection_is_not_cached(storage):
    assert central.active_kb_identity() == ("star_upper_gi", "0.1.2")
    p = storage / "registry.json"
    payload = json.loads(p.read_text())
    payload["active"] = {"module_name": "mst_3_0", "version": "3.0.0"}
    p.write_text(json.dumps(payload))
    assert central.active_kb_identity() == ("mst_3_0", "3.0.0")
    assert central.load_module_kb("mst_3_0").config.version == "3.0.0"
    with pytest.raises(TerminologyError, match="explicit version"):
        central.load_module_kb("star_upper_gi")
    assert (
        central.load_module_kb("star_upper_gi", version="0.1.1.post1").config.version
        == "0.1.1.post1"
    )


@pytest.mark.parametrize(
    "name,version", [("", None), ("star_upper_gi", ""), ("star_upper_gi", " ")]
)
def test_empty_identity_rejected(storage, name, version):
    with pytest.raises(TerminologyError):
        central.load_module_kb(name, version=version)


def payload(**kwargs):
    return builder.SaveReportTemplateRequest(
        module_name="star_upper_gi",
        module_version="0.1.2",
        file_name="central_resolver_test",
        template_name="central_resolver_test",
        examination="gastroscopy",
        **kwargs,
    )


def test_builder_saves_and_reloads_from_hydrated_copy(storage):
    source_before = (package_data_root() / "star_upper_gi/config.yaml").read_bytes()
    saved = builder.save_report_template_definition(payload(), resolved_version="0.1.2")
    assert Path(saved.path).is_relative_to(storage)
    assert Path(saved.path).is_file()
    assert (
        package_data_root() / "star_upper_gi/config.yaml"
    ).read_bytes() == source_before
    clear_knowledge_base_resolver_caches()
    kb = central.load_module_kb("star_upper_gi", version="0.1.2")
    assert "central_resolver_test" in kb.report_template
    central.hydrate_shipped_terminology()
    assert Path(saved.path).is_file()
    assert (
        yaml.safe_load(kb.config.source_file.read_text())["data"]["dirs"][-1]
        == "./generated_templates"
    )


def test_builder_lifecycle_uses_same_directory(storage):
    saved = builder.save_report_template_definition(payload(), resolved_version="0.1.2")
    builder.set_saved_report_template_lifecycle(
        module_name="star_upper_gi",
        module_version="0.1.2",
        template_name=saved.template_name,
        lifecycle_status="published",
    )
    registry = Path(saved.path).parent / "report_template_registry.yaml"
    assert (
        yaml.safe_load(registry.read_text())["templates"][saved.template_name][
            "lifecycle_status"
        ]
        == "published"
    )


def test_builder_duplicate_file_is_not_overwritten(storage):
    saved = builder.save_report_template_definition(payload(), resolved_version="0.1.2")
    before = Path(saved.path).read_bytes()
    with pytest.raises(FileExistsError):
        builder.save_report_template_definition(payload(), resolved_version="0.1.2")
    assert Path(saved.path).read_bytes() == before


def test_builder_version_mismatch_prevents_writes(storage):
    with pytest.raises(ValueError, match="does not match"):
        builder.save_report_template_definition(
            payload(), resolved_version="0.1.1.post1"
        )
    module = central.resolve_module_path("star_upper_gi", version="0.1.2")
    assert not (module / "generated_templates/central_resolver_test.yaml").exists()


def test_builder_override_cannot_redirect_writes(storage):
    with pytest.raises(TerminologyError, match="root conflicts"):
        builder.save_report_template_definition(
            payload(), resolved_version="0.1.2", modules_root=package_data_root()
        )


def test_builder_explicit_historical_location(storage):
    loc = builder.resolve_report_template_module_location(
        "star_upper_gi", "0.1.1.post1"
    )
    assert loc.version == "0.1.1.post1"
    assert loc.modules_root.parts[-3:] == ("versions", "star_upper_gi", "0.1.1.post1")


def test_package_provider_cannot_be_written_before_hydration(storage):
    # The service is already initialized; simulate a registry edit to the package root.
    service = central.get_terminology_service()
    p = service.registry_path
    data = json.loads(p.read_text())
    data["modules"]["star_upper_gi"]["0.1.2"] = {
        "input_dirs": [str(package_data_root())]
    }
    p.write_text(json.dumps(data))
    clear_knowledge_base_resolver_caches()
    with pytest.raises(TerminologyError, match="read-only"):
        builder.save_report_template_definition(payload(), resolved_version="0.1.2")


@pytest.mark.parametrize("name", ["../escape", ".", "..", "a/b", "a\\b", ""])
def test_module_dir_rejects_unsafe_names(storage, name):
    with pytest.raises(ValueError):
        builder.module_dir(name, modules_root=storage)


def test_generated_directory_symlink_escape_is_rejected(storage, tmp_path):
    module = central.resolve_module_path("star_upper_gi", version="0.1.2")
    target = tmp_path / "escape"
    target.mkdir()
    (module / "generated_templates").symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="inside its module"):
        builder.save_report_template_definition(payload(), resolved_version="0.1.2")
    assert list(target.iterdir()) == []


def test_missing_registered_version_is_not_replaced_with_shipped_default(storage):
    with pytest.raises(TerminologyError) as exc:
        central.load_module_kb("star_upper_gi", version="does-not-exist")
    assert exc.value.status == 404


def test_existing_registry_without_active_selection_is_not_reset(storage):
    service = central.get_terminology_service()
    value = json.loads(service.registry_path.read_text())
    value["active"] = None
    service.registry_path.write_text(json.dumps(value))
    service.provision()
    with pytest.raises(TerminologyError, match="No active"):
        central.active_kb_identity()
