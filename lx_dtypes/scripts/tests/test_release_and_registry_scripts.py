from __future__ import annotations

import json
from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch

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
    )

    payload = json.loads(registry_path.read_text())
    assert payload == {
        "modules": {
            "report_template_examples": {
                "0.1.0": {
                    "input_dirs": [str(data_root.resolve())],
                }
            }
        }
    }


def test_write_project_version_updates_pyproject(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path
    pyproject_path = project_root / "pyproject.toml"
    pyproject_path.write_text('[project]\nname = "lx-dtypes"\nversion = "0.1.1"\n')

    monkeypatch.chdir(project_root)

    import lx_dtypes.scripts.release as release_module

    monkeypatch.setattr(release_module, "_project_root", lambda: project_root)
    monkeypatch.setattr(release_module, "_pyproject_path", lambda: pyproject_path)
    monkeypatch.setattr(
        release_module,
        "_init_path",
        lambda: project_root / "lx_dtypes" / "__init__.py",
    )

    assert read_project_version() == "0.1.1"
    write_project_version("0.1.2")
    assert read_project_version() == "0.1.2"
