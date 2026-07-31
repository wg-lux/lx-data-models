from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

from _pytest.monkeypatch import MonkeyPatch
import pytest

from lx_dtypes.scripts.kb_registry import _add_entry
from lx_dtypes.scripts.release import (
    read_project_version,
    write_project_version,
)


def test_add_entry_writes_expected_registry_shape(tmp_path: Path) -> None:
    registry_path = tmp_path / "kb_registry.json"
    data_root = tmp_path / "data"
    data_root.mkdir()

    _add_entry(
        registry_path=registry_path,
        module_name="report_template_examples",
        version="0.1.0",
        input_dirs=[data_root],
        medical_field="gastroenterology",
    )

    payload = json.loads(registry_path.read_text())
    assert payload == {
        "modules": {
            "report_template_examples": {
                "0.1.0": {
                    "input_dirs": [str(data_root.resolve())],
                    "medical_field": "gastroenterology",
                }
            }
        }
    }


def test_add_entry_can_activate_registered_identity(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    from lx_dtypes.scripts import kb_registry

    registry_path = tmp_path / "kb_registry.json"
    data_root = tmp_path / "data"
    data_root.mkdir()
    monkeypatch.setattr(
        kb_registry,
        "load_knowledge_base",
        lambda module_name, *, input_dirs: object(),
    )
    monkeypatch.setattr(
        kb_registry,
        "load_module_config",
        lambda module_name, *, input_dirs: SimpleNamespace(
            name=module_name,
            version="0.1.0",
        ),
    )

    _add_entry(
        registry_path=registry_path,
        module_name="report_template_examples",
        version="0.1.0",
        input_dirs=[data_root],
        activate=True,
    )

    payload = json.loads(registry_path.read_text())
    assert payload["active"] == {
        "module_name": "report_template_examples",
        "version": "0.1.0",
    }


def test_activation_rejects_identity_mismatch_without_replacing_registry(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    from lx_dtypes.scripts import kb_registry

    registry_path = tmp_path / "kb_registry.json"
    original = '{"modules": {}}\n'
    registry_path.write_text(original, encoding="utf-8")
    monkeypatch.setattr(
        kb_registry,
        "load_module_config",
        lambda module_name, *, input_dirs: SimpleNamespace(
            name=module_name,
            version="0.2.0",
        ),
    )

    with pytest.raises(SystemExit, match="expected report_template_examples@0.1.0"):
        _add_entry(
            registry_path=registry_path,
            module_name="report_template_examples",
            version="0.1.0",
            input_dirs=[tmp_path],
            activate=True,
        )

    assert registry_path.read_text(encoding="utf-8") == original


def test_registry_write_preserves_existing_file_when_replace_fails(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    from lx_dtypes.scripts import kb_registry

    registry_path = tmp_path / "kb_registry.json"
    original = '{"modules": {}}\n'
    registry_path.write_text(original, encoding="utf-8")

    def fail_replace(source: os.PathLike[str], destination: os.PathLike[str]) -> None:
        del source, destination
        raise OSError("simulated replace failure")

    monkeypatch.setattr(kb_registry.os, "replace", fail_replace)

    try:
        _add_entry(
            registry_path=registry_path,
            module_name="report_template_examples",
            version="0.1.0",
            input_dirs=[tmp_path],
        )
    except OSError as exc:
        assert str(exc) == "simulated replace failure"
    else:
        raise AssertionError("Expected the simulated atomic replace failure.")

    assert registry_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob(".kb_registry.json.*.tmp"))


def test_write_project_version_updates_pyproject(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path
    pyproject_path = project_root / "pyproject.toml"
    pyproject_path.write_text('[project]\nname = "lx-dtypes"\nversion = "0.1.1"\n')
    kb_config_path = (
        project_root / "lx_dtypes" / "data" / "star_upper_gi" / "config.yaml"
    )
    kb_config_path.parent.mkdir(parents=True)
    kb_config_path.write_text("name: star_upper_gi\nversion: 0.1.1\n")
    demo_kb_config_path = project_root / "demo-data" / "star_upper_gi" / "config.yaml"
    demo_kb_config_path.parent.mkdir(parents=True)
    demo_kb_config_path.write_text("name: star_upper_gi\nversion: 0.1.1\n")
    kb_package_path = project_root / "package.nix"
    kb_package_path.write_text('version = "0.1.1";\nkbModuleVersion = "0.1.1";\n')

    monkeypatch.chdir(project_root)

    import lx_dtypes.scripts.release as release_module

    monkeypatch.setattr(release_module, "_project_root", lambda: project_root)
    monkeypatch.setattr(release_module, "_pyproject_path", lambda: pyproject_path)
    monkeypatch.setattr(
        release_module,
        "_init_path",
        lambda: project_root / "lx_dtypes" / "__init__.py",
    )
    monkeypatch.setattr(
        release_module,
        "_kb_config_paths",
        lambda: (kb_config_path, demo_kb_config_path),
    )
    monkeypatch.setattr(
        release_module,
        "_kb_package_path",
        lambda: kb_package_path,
    )

    assert read_project_version() == "0.1.1"
    write_project_version("0.1.2")
    assert read_project_version() == "0.1.2"
    assert "version: 0.1.2" in kb_config_path.read_text()
    assert "version: 0.1.2" in demo_kb_config_path.read_text()
    assert 'version = "0.1.2";' in kb_package_path.read_text()
    assert 'kbModuleVersion = "0.1.2";' in kb_package_path.read_text()
