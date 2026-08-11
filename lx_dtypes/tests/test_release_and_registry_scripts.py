from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from _pytest.capture import CaptureFixture
from _pytest.monkeypatch import MonkeyPatch

from lx_dtypes.scripts.kb_registry import _add_entry
from lx_dtypes.scripts.release import (
    cmd_build,
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


def test_write_project_version_does_not_rewrite_kb_module_versions(
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
    assert read_project_version() == "0.1.1"
    write_project_version("0.1.2")
    assert read_project_version() == "0.1.2"
    assert "version: 0.1.1" in kb_config_path.read_text()
    assert "version: 0.1.1" in demo_kb_config_path.read_text()
    assert 'version = "0.1.1";' in kb_package_path.read_text()
    assert 'kbModuleVersion = "0.1.1";' in kb_package_path.read_text()


def test_cmd_build_checks_only_current_version_artifacts(
    monkeypatch: MonkeyPatch, tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "lx-dtypes"\nversion = "0.2.14"\n'
    )
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    old_wheel = dist_dir / "lx_dtypes-0.2.13-py3-none-any.whl"
    current_wheel = dist_dir / "lx_dtypes-0.2.14-py3-none-any.whl"
    current_sdist = dist_dir / "lx_dtypes-0.2.14.tar.gz"
    for artifact in (old_wheel, current_wheel, current_sdist):
        artifact.touch()

    import lx_dtypes.scripts.release as release_module

    commands: list[list[str]] = []
    monkeypatch.setattr(release_module, "_project_root", lambda: tmp_path)
    monkeypatch.setattr(
        release_module, "_pyproject_path", lambda: tmp_path / "pyproject.toml"
    )
    monkeypatch.setattr(
        release_module,
        "run_command",
        lambda args, *, cwd: commands.append(args),
    )

    assert cmd_build(Namespace()) == 0
    assert commands[1][-2:] == [str(current_wheel), str(current_sdist)]
    assert str(old_wheel) not in commands[1]
    output = capsys.readouterr().out
    assert "lx-dtypes 0.2.14 artifacts only" in output
    assert "do not upload dist/*" in output
