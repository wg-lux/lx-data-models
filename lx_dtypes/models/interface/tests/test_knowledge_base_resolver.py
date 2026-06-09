from __future__ import annotations

import json
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


def test_resolve_default_data_root_prefers_configured_lookup_root(
    monkeypatch: pytest.MonkeyPatch,
    settings: Any,
    tmp_path: Path,
) -> None:
    configured_root = tmp_path / "configured-data"
    configured_root.mkdir(parents=True)
    settings.LOOKUP_DTYPES_DATA_ROOT = str(configured_root)

    resolved_root = resolve_default_data_root()

    assert resolved_root == configured_root.resolve()
