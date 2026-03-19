from __future__ import annotations

import json
from pathlib import Path

import pytest

from lx_dtypes.models.interface.KnowledgeBaseResolver import (
    KnowledgeBaseVersionNotFoundError,
    clear_knowledge_base_resolver_caches,
    load_knowledge_base,
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
