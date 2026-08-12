from __future__ import annotations

import json
import tarfile
import zipfile
from argparse import Namespace
from io import BytesIO
from pathlib import Path

import pytest
from _pytest.capture import CaptureFixture
from _pytest.monkeypatch import MonkeyPatch

from lx_dtypes.scripts.kb_registry import _add_entry
from lx_dtypes.scripts.release import (
    cmd_build,
    read_project_version,
    verify_migration_artifacts,
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
    verified_artifacts: list[Path] = []
    monkeypatch.setattr(
        release_module,
        "verify_migration_artifacts",
        lambda root, *, version, artifacts: verified_artifacts.extend(artifacts),
    )

    assert cmd_build(Namespace()) == 0
    assert verified_artifacts == [current_wheel, current_sdist]
    assert commands[1][-2:] == [str(current_wheel), str(current_sdist)]
    assert str(old_wheel) not in commands[1]
    output = capsys.readouterr().out
    assert "lx-dtypes 0.2.14 artifacts only" in output
    assert "do not upload dist/*" in output


def _write_release_artifacts(
    root: Path,
    *,
    version: str,
    include_migration: bool = True,
    artifact_migration_contents: bytes | None = None,
) -> list[Path]:
    migration_root = root / "lx_dtypes" / "django" / "migrations"
    migration_root.mkdir(parents=True)
    migration_contents = b"from django.db import migrations\n"
    migration_path = migration_root / "0001_initial.py"
    migration_path.write_bytes(migration_contents)
    (migration_root / "max_migration.txt").write_text("0001_initial\n")
    packaged_migration_contents = artifact_migration_contents or migration_contents

    wheel = root / f"lx_dtypes-{version}-py3-none-any.whl"
    with zipfile.ZipFile(wheel, mode="w") as archive:
        if include_migration:
            archive.writestr(
                "lx_dtypes/django/migrations/0001_initial.py",
                packaged_migration_contents,
            )
        archive.writestr(
            "lx_dtypes/django/migrations/max_migration.txt",
            "0001_initial\n",
        )

    sdist = root / f"lx_dtypes-{version}.tar.gz"
    with tarfile.open(sdist, mode="w:gz") as archive:
        files = {
            "lx_dtypes/django/migrations/max_migration.txt": b"0001_initial\n",
        }
        if include_migration:
            files["lx_dtypes/django/migrations/0001_initial.py"] = (
                packaged_migration_contents
            )
        for relative_path, contents in files.items():
            info = tarfile.TarInfo(f"lx_dtypes-{version}/{relative_path}")
            info.size = len(contents)
            archive.addfile(info, BytesIO(contents))
    return [wheel, sdist]


def test_verify_migration_artifacts_matches_source_tree(tmp_path: Path) -> None:
    artifacts = _write_release_artifacts(tmp_path, version="0.2.16")

    verify_migration_artifacts(
        tmp_path,
        version="0.2.16",
        artifacts=artifacts,
    )


def test_verify_migration_artifacts_rejects_packaging_omission(
    tmp_path: Path,
) -> None:
    artifacts = _write_release_artifacts(
        tmp_path,
        version="0.2.16",
        include_migration=False,
    )

    with pytest.raises(SystemExit, match="missing migration"):
        verify_migration_artifacts(
            tmp_path,
            version="0.2.16",
            artifacts=artifacts,
        )


def test_verify_migration_artifacts_rejects_content_drift(tmp_path: Path) -> None:
    artifacts = _write_release_artifacts(
        tmp_path,
        version="0.2.16",
        artifact_migration_contents=b"from django.db import models\n",
    )

    with pytest.raises(SystemExit, match="differs from the source tree"):
        verify_migration_artifacts(
            tmp_path,
            version="0.2.16",
            artifacts=artifacts,
        )
