from __future__ import annotations

import builtins
import json
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest

from lx_dtypes.knowledge_bases import (
    BUILTIN_KNOWLEDGE_BASE_PROVIDER,
    get_packaged_knowledge_base,
)
from lx_dtypes.models.interface.KnowledgeBaseResolver import (
    KnowledgeBaseIdentityRequiredError,
    KnowledgeBaseRegistryError,
    KnowledgeBaseVersionConflictError,
    KnowledgeBaseVersionNotFoundError,
    clear_knowledge_base_resolver_caches,
    get_knowledge_base_identity,
    load_knowledge_base,
    load_module_config,
    resolve_default_data_root,
)
from lx_dtypes.models.interface import remote_data_roots
from lx_dtypes.models.interface.data_roots import package_data_root


def _write_kb_root(root: Path, *, module_name: str, version: str) -> None:
    module_dir = root / module_name
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "config.yaml").write_text(
        "\n".join(
            [
                f"name: {module_name}",
                "description: Versioned test module",
                f"version: {version}",
                "depends_on: []",
                "modules: []",
                "data:",
                "  dirs: []",
            ]
        )
        + "\n"
    )


def _write_unit_module(
    module_dir: Path,
    *,
    module_name: str,
    unit_name: str,
    child_modules: tuple[str, ...] = (),
) -> None:
    module_dir.mkdir(parents=True, exist_ok=True)
    modules_yaml = (
        "modules:\n" + "".join(f"  - {name}\n" for name in child_modules)
        if child_modules
        else "modules: []\n"
    )
    (module_dir / "config.yaml").write_text(
        "".join(
            [
                f"name: {module_name}\n",
                "description: Resolver structure test module\n",
                "version: 1.0.0\n",
                modules_yaml,
                "depends_on: []\n",
                "data:\n",
                "  dirs:\n",
                "    - ./data\n",
            ]
        )
    )
    data_dir = module_dir / "data"
    data_dir.mkdir()
    (data_dir / "unit.yaml").write_text(
        f"- model: unit\n  name: {unit_name}\n  abbreviation: u\n"
    )


def _write_filesystem_registry(
    registry_path: Path,
    *,
    module_name: str,
    version: str,
    input_dir: Path,
) -> None:
    registry_path.write_text(
        json.dumps(
            {
                "modules": {
                    module_name: {
                        version: {
                            "sources": [
                                {
                                    "kind": "filesystem",
                                    "input_dirs": [str(input_dir)],
                                }
                            ]
                        }
                    }
                }
            }
        )
    )


def _write_scoped_unit_bundle(root: Path) -> None:
    canonical_units_dir = root / "terminology" / "lx_units"
    canonical_units_dir.mkdir(parents=True, exist_ok=True)
    (canonical_units_dir / "config.yaml").write_text(
        "\n".join(
            [
                "name: lx_units",
                'description: ""',
                "version: 0.1.0",
                "modules: []",
                "depends_on: []",
                "data:",
                "  dirs:",
                "    - ./data",
            ]
        )
        + "\n"
    )
    (canonical_units_dir / "data").mkdir(parents=True, exist_ok=True)
    (canonical_units_dir / "data" / "units.yaml").write_text(
        "- model: unit\n  name: canonical_centimeter\n  abbreviation: cm\n"
    )

    editor_bundle_dir = root / "editor_bundle"
    editor_bundle_dir.mkdir(parents=True, exist_ok=True)
    (editor_bundle_dir / "config.yaml").write_text(
        "\n".join(
            [
                "name: editor_bundle",
                'description: ""',
                "version: 0.1.0",
                "modules:",
                "  - lx_units",
                "depends_on: []",
                "data:",
                "  dirs: []",
            ]
        )
        + "\n"
    )

    editor_units_dir = editor_bundle_dir / "lx_units"
    editor_units_dir.mkdir(parents=True, exist_ok=True)
    (editor_units_dir / "config.yaml").write_text(
        "\n".join(
            [
                "name: lx_units",
                'description: ""',
                "version: 0.1.0",
                "modules: []",
                "depends_on: []",
                "data:",
                "  dirs:",
                "    - ./data",
            ]
        )
        + "\n"
    )
    (editor_units_dir / "data").mkdir(parents=True, exist_ok=True)
    (editor_units_dir / "data" / "units.yaml").write_text(
        "- model: unit\n  name: editor_millimeter\n  abbreviation: mm\n"
    )


def test_load_knowledge_base_uses_versioned_registry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module_name = "versioned_demo_module"
    root_v1 = tmp_path / "v1"
    root_v2 = tmp_path / "v2"
    _write_kb_root(root_v1, module_name=module_name, version="0.1.0")
    _write_kb_root(root_v2, module_name=module_name, version="0.2.0")

    registry_path = tmp_path / "kb_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "modules": {
                    module_name: {
                        "0.1.0": str(root_v1),
                        "0.2.0": {"input_dirs": [str(root_v2)]},
                    }
                }
            }
        )
    )

    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))
    clear_knowledge_base_resolver_caches()
    try:
        kb_v1 = load_knowledge_base(module_name, version="0.1.0")
        kb_v2 = load_knowledge_base(module_name, version="0.2.0")
    finally:
        clear_knowledge_base_resolver_caches()

    assert kb_v1.config.name == module_name
    assert kb_v1.config.version == "0.1.0"
    assert kb_v2.config.name == module_name
    assert kb_v2.config.version == "0.2.0"


def test_resolver_merges_multiple_modules_into_one_knowledge_base(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    bundle_root = tmp_path / "merged-bundle"
    root_name = "merged_root"
    child_names = ("cardiology_module", "gastroenterology_module")
    root_dir = bundle_root / root_name
    _write_unit_module(
        root_dir,
        module_name=root_name,
        unit_name="unit_from_root",
        child_modules=child_names,
    )
    _write_unit_module(
        root_dir / child_names[0],
        module_name=child_names[0],
        unit_name="unit_from_cardiology",
    )
    _write_unit_module(
        root_dir / child_names[1],
        module_name=child_names[1],
        unit_name="unit_from_gastroenterology",
    )

    registry_path = tmp_path / "merged-registry.json"
    _write_filesystem_registry(
        registry_path,
        module_name=root_name,
        version="1.0.0",
        input_dir=bundle_root,
    )
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))
    clear_knowledge_base_resolver_caches()
    try:
        knowledge_base = load_knowledge_base(root_name, version="1.0.0")
    finally:
        clear_knowledge_base_resolver_caches()

    assert knowledge_base.config.name == root_name
    assert knowledge_base.config.modules == list(child_names)
    assert set(knowledge_base.unit) == {
        "unit_from_root",
        "unit_from_cardiology",
        "unit_from_gastroenterology",
    }


def test_resolver_loads_very_deep_nested_module_structure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    depth = 48
    bundle_root = tmp_path / "deep-bundle"
    module_names = ["deep_root", *(f"deep_{index:02d}" for index in range(depth))]
    module_dir = bundle_root / module_names[0]
    for index, module_name in enumerate(module_names):
        children = (module_names[index + 1],) if index + 1 < len(module_names) else ()
        _write_unit_module(
            module_dir,
            module_name=module_name,
            unit_name=f"unit_{module_name}",
            child_modules=children,
        )
        if children:
            module_dir = module_dir / children[0]

    registry_path = tmp_path / "deep-registry.json"
    _write_filesystem_registry(
        registry_path,
        module_name=module_names[0],
        version="1.0.0",
        input_dir=bundle_root,
    )
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))
    clear_knowledge_base_resolver_caches()
    try:
        knowledge_base = load_knowledge_base(module_names[0], version="1.0.0")
    finally:
        clear_knowledge_base_resolver_caches()

    assert set(knowledge_base.unit) == {
        f"unit_{module_name}" for module_name in module_names
    }
    assert knowledge_base.config.modules == module_names[1:]


def test_resolver_loads_very_broad_module_structure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    width = 128
    bundle_root = tmp_path / "broad-bundle"
    root_name = "broad_root"
    child_names = tuple(f"broad_{index:03d}" for index in range(width))
    root_dir = bundle_root / root_name
    _write_unit_module(
        root_dir,
        module_name=root_name,
        unit_name="unit_broad_root",
        child_modules=child_names,
    )
    for child_name in child_names:
        _write_unit_module(
            root_dir / child_name,
            module_name=child_name,
            unit_name=f"unit_{child_name}",
        )

    registry_path = tmp_path / "broad-registry.json"
    _write_filesystem_registry(
        registry_path,
        module_name=root_name,
        version="1.0.0",
        input_dir=bundle_root,
    )
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))
    clear_knowledge_base_resolver_caches()
    try:
        knowledge_base = load_knowledge_base(root_name, version="1.0.0")
    finally:
        clear_knowledge_base_resolver_caches()

    assert set(knowledge_base.unit) == {
        "unit_broad_root",
        *(f"unit_{child_name}" for child_name in child_names),
    }
    assert knowledge_base.config.modules == list(child_names)


def test_load_module_config_resolves_packaged_provider_at_runtime(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    descriptor = get_packaged_knowledge_base("star_upper_gi", "0.1.2")
    registry_path = tmp_path / "kb_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "modules": {
                    descriptor.module_name: {
                        descriptor.version: {
                            "sources": [
                                {
                                    "kind": "provider",
                                    "provider": BUILTIN_KNOWLEDGE_BASE_PROVIDER,
                                    "content_sha256": descriptor.content_sha256,
                                }
                            ]
                        }
                    }
                }
            }
        )
    )
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))
    clear_knowledge_base_resolver_caches()
    try:
        config = load_module_config(descriptor.module_name, version=descriptor.version)
    finally:
        clear_knowledge_base_resolver_caches()

    assert config.name == descriptor.module_name
    assert config.version == descriptor.version


def test_packaged_provider_rejects_registered_digest_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    descriptor = get_packaged_knowledge_base("star_upper_gi", "0.1.2")
    registry_path = tmp_path / "kb_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "modules": {
                    descriptor.module_name: {
                        descriptor.version: {
                            "sources": [
                                {
                                    "kind": "provider",
                                    "provider": BUILTIN_KNOWLEDGE_BASE_PROVIDER,
                                    "content_sha256": "0" * 64,
                                }
                            ]
                        }
                    }
                }
            }
        )
    )
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))
    clear_knowledge_base_resolver_caches()
    try:
        with pytest.raises(KnowledgeBaseVersionConflictError, match="digest"):
            load_module_config(descriptor.module_name, version=descriptor.version)
    finally:
        clear_knowledge_base_resolver_caches()


def test_packaged_provider_rejects_unknown_provider(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "kb_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "modules": {
                    "star_upper_gi": {
                        "0.1.2": {
                            "sources": [
                                {
                                    "kind": "provider",
                                    "provider": "unknown.provider",
                                    "content_sha256": "0" * 64,
                                }
                            ]
                        }
                    }
                }
            }
        )
    )
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))
    clear_knowledge_base_resolver_caches()
    try:
        with pytest.raises(KnowledgeBaseRegistryError, match="Unknown.*provider"):
            load_module_config("star_upper_gi", version="0.1.2")
    finally:
        clear_knowledge_base_resolver_caches()


def test_load_module_config_materializes_github_tree_registry_source(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module_name = "remote_demo_module"
    archive_buffer = BytesIO()
    with zipfile.ZipFile(archive_buffer, "w") as archive:
        archive.writestr(
            f"lx-data-models-main/demo-data/{module_name}/config.yaml",
            "\n".join(
                [
                    f"name: {module_name}",
                    "description: Remote test module",
                    "version: 0.1.0",
                    "depends_on: []",
                    "modules: []",
                    "data:",
                    "  dirs: []",
                ]
            )
            + "\n",
        )

    class _ArchiveResponse:
        def raise_for_status(self) -> None:
            return None

        def iter_content(self, *, chunk_size: int):
            del chunk_size
            yield archive_buffer.getvalue()

    monkeypatch.setenv("LX_DTYPES_REMOTE_CACHE_ROOT", str(tmp_path / "cache"))
    monkeypatch.setattr(
        remote_data_roots.requests,
        "get",
        lambda *args, **kwargs: _ArchiveResponse(),
    )
    registry_path = tmp_path / "kb_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "modules": {
                    module_name: {
                        "0.1.0": {
                            "input_dirs": [
                                "https://github.com/wg-lux/lx-data-models/"
                                f"tree/main/demo-data/{module_name}"
                            ]
                        }
                    }
                }
            }
        )
    )
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))
    clear_knowledge_base_resolver_caches()
    try:
        config = load_module_config(module_name, version="0.1.0")
    finally:
        clear_knowledge_base_resolver_caches()

    assert config.name == module_name
    assert config.version == "0.1.0"
    assert (tmp_path / "cache").is_dir()


def test_remote_data_root_filesystem_operations_do_not_import_endoreg_db(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_import = builtins.__import__

    def _reject_endoreg_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "endoreg_db" or name.startswith("endoreg_db."):
            raise AssertionError(f"unexpected reverse runtime dependency: {name}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _reject_endoreg_import)

    operations = remote_data_roots._filesystem_operations()

    assert operations.atomic_write_file is remote_data_roots._atomic_write_file
    assert operations.atomic_move_path is remote_data_roots._atomic_move_path


def test_atomic_remote_cache_write_preserves_existing_file_on_failure(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "cache" / "config.yaml"
    destination.parent.mkdir()
    destination.write_bytes(b"existing")

    def _failing_content():
        yield b"replacement"
        raise RuntimeError("interrupted write")

    with pytest.raises(RuntimeError, match="interrupted write"):
        remote_data_roots._atomic_write_file(
            destination=destination,
            content=_failing_content(),
            required_bytes=len(b"replacement"),
            file_mode=0o640,
            dir_mode=0o750,
        )

    assert destination.read_bytes() == b"existing"
    assert list(destination.parent.glob(f".{destination.name}.*.tmp")) == []


def test_load_knowledge_base_uses_bundle_scoped_duplicate_modules(
    tmp_path: Path,
) -> None:
    _write_scoped_unit_bundle(tmp_path)

    kb = load_knowledge_base("editor_bundle", input_dirs=[tmp_path])

    assert "editor_millimeter" in kb.unit
    assert "canonical_centimeter" not in kb.unit


def test_load_knowledge_base_raises_for_unprovisioned_version(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module_name = "versioned_demo_module"
    root_v1 = tmp_path / "v1"
    _write_kb_root(root_v1, module_name=module_name, version="0.1.0")

    registry_path = tmp_path / "kb_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "modules": {
                    module_name: {
                        "0.1.0": str(root_v1),
                    }
                }
            }
        )
    )

    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))
    clear_knowledge_base_resolver_caches()
    try:
        with pytest.raises(
            KnowledgeBaseVersionNotFoundError,
            match="not provisioned locally",
        ):
            load_knowledge_base(module_name, version="9.9.9")
    finally:
        clear_knowledge_base_resolver_caches()


def test_registry_cache_observes_external_atomic_registry_replacement(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module_name = "externally_replaced_module"
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    _write_unit_module(
        first_root / module_name,
        module_name=module_name,
        unit_name="unit_from_first_registry",
    )
    _write_unit_module(
        second_root / module_name,
        module_name=module_name,
        unit_name="unit_from_replaced_registry",
    )
    registry_path = tmp_path / "kb_registry.json"
    _write_filesystem_registry(
        registry_path,
        module_name=module_name,
        version="1.0.0",
        input_dir=first_root,
    )

    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))
    clear_knowledge_base_resolver_caches()
    try:
        first = load_knowledge_base(module_name, version="1.0.0")

        replacement_path = tmp_path / "replacement.json"
        _write_filesystem_registry(
            replacement_path,
            module_name=module_name,
            version="1.0.0",
            input_dir=second_root,
        )
        replacement_path.replace(registry_path)

        replaced = load_knowledge_base(module_name, version="1.0.0")
    finally:
        clear_knowledge_base_resolver_caches()

    assert set(first.unit) == {"unit_from_first_registry"}
    assert set(replaced.unit) == {"unit_from_replaced_registry"}


def test_configured_registry_never_falls_back_to_default_data_roots(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module_name = "checkout_only_module"
    default_root = tmp_path / "checkout"
    _write_kb_root(default_root, module_name=module_name, version="0.1.0")
    registry_path = tmp_path / "kb_registry.json"
    registry_path.write_text(json.dumps({"modules": {}}))

    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))
    monkeypatch.setattr(
        "lx_dtypes.models.interface.KnowledgeBaseResolver._default_input_dirs",
        lambda: (default_root,),
    )
    clear_knowledge_base_resolver_caches()
    try:
        with pytest.raises(KnowledgeBaseVersionNotFoundError):
            load_knowledge_base(module_name, version="0.1.0")
    finally:
        clear_knowledge_base_resolver_caches()


def test_configured_registry_requires_explicit_module_version(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module_name = "versioned_demo_module"
    root = tmp_path / "bundle"
    _write_kb_root(root, module_name=module_name, version="0.1.0")
    registry_path = tmp_path / "kb_registry.json"
    registry_path.write_text(
        json.dumps({"modules": {module_name: {"0.1.0": {"input_dirs": [str(root)]}}}})
    )

    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))
    clear_knowledge_base_resolver_caches()
    try:
        with pytest.raises(
            KnowledgeBaseIdentityRequiredError,
            match="module@version",
        ):
            load_module_config(module_name)
    finally:
        clear_knowledge_base_resolver_caches()


def test_registry_artifact_identity_conflict_is_typed_and_loud(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module_name = "versioned_demo_module"
    root = tmp_path / "bundle"
    _write_kb_root(root, module_name=module_name, version="0.1.0")
    registry_path = tmp_path / "kb_registry.json"
    registry_path.write_text(
        json.dumps({"modules": {module_name: {"0.2.0": str(root)}}})
    )

    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))
    clear_knowledge_base_resolver_caches()
    try:
        with pytest.raises(
            KnowledgeBaseVersionConflictError,
            match="0.1.0.*0.2.0",
        ):
            load_knowledge_base(module_name, version="0.2.0")
    finally:
        clear_knowledge_base_resolver_caches()


def test_load_module_config_returns_current_module_config(tmp_path: Path) -> None:
    module_name = "versioned_demo_module"
    _write_kb_root(tmp_path, module_name=module_name, version="0.1.0")

    module_config = load_module_config(module_name, input_dirs=[tmp_path])

    assert module_config.name == module_name
    assert module_config.version == "0.1.0"


def test_get_knowledge_base_identity_uses_loaded_module_version(tmp_path: Path) -> None:
    module_name = "versioned_demo_module"
    _write_kb_root(tmp_path, module_name=module_name, version="0.1.0")

    identity = get_knowledge_base_identity(module_name, input_dirs=[tmp_path])

    assert identity == (module_name, "0.1.0")


def test_get_knowledge_base_identity_validates_explicit_version(tmp_path: Path) -> None:
    module_name = "versioned_demo_module"
    _write_kb_root(tmp_path, module_name=module_name, version="0.1.0")

    with pytest.raises(KnowledgeBaseVersionConflictError):
        get_knowledge_base_identity(
            module_name,
            version="9.9.9",
            input_dirs=[tmp_path],
        )


def test_resolve_default_data_root_ignores_runtime_overlays(
    settings: Any,
    tmp_path: Path,
) -> None:
    configured_root = tmp_path / "configured-data"
    configured_root.mkdir(parents=True)
    settings.LOOKUP_DTYPES_DATA_ROOT = str(configured_root)

    resolved_root = resolve_default_data_root()

    assert resolved_root == package_data_root()
