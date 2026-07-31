from __future__ import annotations

import builtins
import json
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest

from lx_dtypes.models.interface.KnowledgeBaseResolver import (
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


def test_get_knowledge_base_identity_prefers_explicit_version(tmp_path: Path) -> None:
    module_name = "versioned_demo_module"
    _write_kb_root(tmp_path, module_name=module_name, version="0.1.0")

    identity = get_knowledge_base_identity(
        module_name,
        version="9.9.9",
        input_dirs=[tmp_path],
    )

    assert identity == (module_name, "9.9.9")


def test_resolve_default_data_root_ignores_runtime_overlays(
    settings: Any,
    tmp_path: Path,
) -> None:
    configured_root = tmp_path / "configured-data"
    configured_root.mkdir(parents=True)
    settings.LOOKUP_DTYPES_DATA_ROOT = str(configured_root)

    resolved_root = resolve_default_data_root()

    assert resolved_root == package_data_root()
