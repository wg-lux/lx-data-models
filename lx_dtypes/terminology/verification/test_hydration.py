from __future__ import annotations

import json
import logging
import multiprocessing
import shutil
from pathlib import Path

import pytest
import yaml

from lx_dtypes.knowledge_bases import (
    BUILTIN_KNOWLEDGE_BASE_PROVIDER,
    list_packaged_knowledge_bases,
)
from lx_dtypes.models.interface.data_roots import package_data_root
from lx_dtypes.terminology import terminology_loader as central
from lx_dtypes.terminology.hydration import _tree_digest, hydrate_registry
from lx_dtypes.terminology.terminology_service import (
    TerminologyError,
    TerminologyService,
)

logger = logging.getLogger(__name__)


def test_actual_shipped_tree_copied_and_all_catalog_versions_load(seed):
    service = TerminologyService(seed / "registry.json")
    payload = json.loads(service.registry_path.read_text())
    descriptors = list_packaged_knowledge_bases()
    assert len(descriptors) == 7
    assert service.active_identity() == ("star_upper_gi", "0.1.2")
    for d in descriptors:
        entry = payload["modules"][d.module_name][d.version]
        inputs = entry["sources"][0]["input_dirs"]
        assert entry["sources"][0]["kind"] == "filesystem"
        assert Path(inputs[0]).is_relative_to(seed)
        kb = service.load(d.module_name, d.version)
        assert (kb.config.name, kb.config.version) == (d.module_name, d.version)
        assert kb.config.source_file is not None
        assert kb.config.source_file.is_relative_to(seed)
        d.verified_resource_directory()  # original bytes still match the catalog
    data = next((seed / "shipped").iterdir()) / "data"
    assert _tree_digest(data) == _tree_digest(package_data_root())
    assert (data / "terminology/lx_units/config.yaml").is_file()


def test_repeat_hydration_keeps_edited_copy_and_active(storage):
    service = central.get_terminology_service()
    kb = service.load("star_upper_gi", "0.1.2")
    assert kb.config.source_file is not None
    target = kb.config.source_file.parent / "local_note.txt"
    target.write_text("keep this edit")
    payload = json.loads(service.registry_path.read_text())
    payload["active"] = {"module_name": "mst_3_0", "version": "3.0.0"}
    service.registry_path.write_text(json.dumps(payload))
    before = service.registry_path.read_bytes()
    service.provision()
    assert target.read_text() == "keep this edit"
    assert service.registry_path.read_bytes() == before
    assert service.active_identity() == ("mst_3_0", "3.0.0")


def test_existing_custom_source_and_selection_are_preserved(storage):
    service = central.get_terminology_service()
    payload = json.loads(service.registry_path.read_text())
    custom = {
        "sources": [{"kind": "filesystem", "input_dirs": ["/custom/managed/data"]}],
        "note": "preserve",
    }
    payload["modules"]["custom"] = {"1": custom}
    payload["active"] = {"module_name": "custom", "version": "1"}
    service.registry_path.write_text(json.dumps(payload))
    service.provision()
    after = json.loads(service.registry_path.read_text())
    assert after["modules"]["custom"]["1"] == custom
    assert after["active"] == payload["active"]


def test_provider_source_is_migrated_to_copied_tree(storage):
    service = central.get_terminology_service()
    d = next(x for x in list_packaged_knowledge_bases() if x.module_name == "mst_3_0")
    payload = json.loads(service.registry_path.read_text())
    payload["modules"][d.module_name][d.version] = {
        "sources": [
            {
                "kind": "provider",
                "provider": BUILTIN_KNOWLEDGE_BASE_PROVIDER,
                "content_sha256": d.content_sha256,
            }
        ],
        "note": "keep",
    }
    service.registry_path.write_text(json.dumps(payload))
    service.provision()
    entry = json.loads(service.registry_path.read_text())["modules"][d.module_name][
        d.version
    ]
    assert entry["sources"][0]["kind"] == "filesystem"
    assert entry["note"] == "keep"
    assert Path(entry["sources"][0]["input_dirs"][0]).is_relative_to(storage)


def test_bad_provider_digest_fails_without_resetting_registry(storage):
    service = central.get_terminology_service()
    payload = json.loads(service.registry_path.read_text())
    payload["modules"]["mst_3_0"]["3.0.0"] = {
        "sources": [
            {
                "kind": "provider",
                "provider": BUILTIN_KNOWLEDGE_BASE_PROVIDER,
                "content_sha256": "0" * 64,
            }
        ]
    }
    service.registry_path.write_text(json.dumps(payload))
    before = service.registry_path.read_bytes()
    with pytest.raises(TerminologyError, match="digest conflicts"):
        service.provision()
    assert service.registry_path.read_bytes() == before


def test_legacy_exact_package_path_is_migrated(storage):
    service = central.get_terminology_service()
    payload = json.loads(service.registry_path.read_text())
    payload["modules"]["mst_3_0"]["3.0.0"] = {"input_dirs": [str(package_data_root())]}
    service.registry_path.write_text(json.dumps(payload))
    service.provision()
    source_file = service.load("mst_3_0", "3.0.0").config.source_file
    assert source_file is not None
    assert source_file.is_relative_to(storage)


def test_missing_new_identity_is_added_without_overwriting_other_edits(storage):
    service = central.get_terminology_service()
    target = service.load("star_upper_gi", "0.1.2").config.source_file
    assert target is not None
    config = yaml.safe_load(target.read_text())
    config["description"] = "local customization"
    target.write_text(yaml.safe_dump(config, sort_keys=False))
    payload = json.loads(service.registry_path.read_text())
    del payload["modules"]["mst_3_0"]
    service.registry_path.write_text(json.dumps(payload))
    service.provision()
    assert "mst_3_0" in json.loads(service.registry_path.read_text())["modules"]
    assert yaml.safe_load(target.read_text())["description"] == "local customization"


def test_bad_source_digest_is_not_published(tmp_path):
    source = tmp_path / "source"
    shutil.copytree(package_data_root(), source)
    (source / "mst_3_0/data/bad.yaml").write_text("[]")
    service = TerminologyService(tmp_path / "destination/registry.json")
    with pytest.raises(TerminologyError, match="digest mismatch"):
        hydrate_registry(service, source_root=source)
    assert not service.registry_path.exists()
    assert not (service.registry_path.parent / "shipped").exists()


@pytest.mark.parametrize("overlap", ["same", "child", "parent"])
def test_source_and_destination_must_not_overlap(tmp_path, overlap):
    source = tmp_path / "source"
    shutil.copytree(package_data_root(), source)
    root = {"same": source, "child": source / "writable", "parent": tmp_path}[overlap]
    with pytest.raises(TerminologyError, match="must not overlap"):
        hydrate_registry(TerminologyService(root / "registry.json"), source_root=source)


def test_failed_registry_commit_cleans_new_copy(tmp_path, monkeypatch):
    service = TerminologyService(tmp_path / "state/registry.json")

    def fail(self, payload):
        raise OSError("simulated commit failure")

    monkeypatch.setattr(TerminologyService, "_write", fail)
    with pytest.raises(TerminologyError, match="simulated commit failure"):
        service.provision()
    assert not service.registry_path.exists()
    assert list((service.registry_path.parent / "shipped").iterdir()) == []


def test_invalid_registry_is_not_replaced_by_fallback(tmp_path):
    root = tmp_path / "state"
    root.mkdir()
    p = root / "registry.json"
    p.write_text("{bad json")
    with pytest.raises(TerminologyError, match="registry is invalid"):
        TerminologyService(p).provision()
    assert p.read_text() == "{bad json"


def _provision_worker(root, queue):
    try:
        service = TerminologyService(Path(root) / "registry.json")
        service.provision()
        queue.put(service.active_identity())
    except Exception as exc:  # ignore
        queue.put(repr(exc))
        logger.exception("Something went wrong")


def test_two_processes_provision_one_consistent_registry(tmp_path):
    ctx = multiprocessing.get_context("fork")
    queue = ctx.Queue()
    root = tmp_path / "state"
    workers = [
        ctx.Process(target=_provision_worker, args=(str(root), queue)) for _ in range(2)
    ]
    for p in workers:
        p.start()
    try:
        results = [queue.get(timeout=40) for _ in workers]
        for p in workers:
            p.join(10)
        assert results == [("star_upper_gi", "0.1.2")] * 2
        assert len(list((root / "shipped").iterdir())) == 1
        assert all(p.exitcode == 0 for p in workers)
    finally:
        for p in workers:
            if p.is_alive():
                p.terminate()
                p.join()


def test_copy_of_read_only_source_gets_owner_write_permission(tmp_path):
    source = tmp_path / "source"
    shutil.copytree(package_data_root(), source)
    original = source / "star_upper_gi/config.yaml"
    original.chmod(0o444)
    service = TerminologyService(tmp_path / "destination/registry.json")
    hydrate_registry(service, source_root=source)
    target = service.load("star_upper_gi", "0.1.2").config.source_file
    assert target is not None
    assert target.stat().st_mode & 0o200
    assert not original.stat().st_mode & 0o200
    assert target.read_bytes() == original.read_bytes()


def test_source_symlink_is_not_followed(tmp_path):
    source = tmp_path / "source"
    shutil.copytree(package_data_root(), source)
    (source / "escape").symlink_to(tmp_path, target_is_directory=True)
    service = TerminologyService(tmp_path / "destination/registry.json")
    with pytest.raises(TerminologyError, match="symlinks"):
        hydrate_registry(service, source_root=source)
    assert not service.registry_path.exists()
