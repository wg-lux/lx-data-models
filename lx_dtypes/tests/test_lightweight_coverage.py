from __future__ import annotations

import argparse
import json
import tomllib
from pathlib import Path

import pytest

from lx_dtypes.models import main as models_main
from lx_dtypes.scripts import kb_registry, lint_kb_yaml, release
from lx_dtypes.serialization.path import serialize_path


def test_models_main_exports_are_populated() -> None:
    assert models_main.MODEL_NAMES
    assert "Citation" in models_main.MODEL_NAMES
    assert "Patient" in models_main.MODEL_NAMES
    assert models_main.MODELS is not None
    assert models_main.MODELS_DJANGO is not None
    assert models_main.DDICTS is not None


def test_serialize_path_handles_values_and_none(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "file.txt"
    assert serialize_path(path) == path.as_posix()
    assert serialize_path(None) is None


def test_wheel_build_includes_knowledge_base_data() -> None:
    payload = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    wheel_force_include = payload["tool"]["hatch"]["build"]["targets"]["wheel"][
        "force-include"
    ]

    assert wheel_force_include["lx_dtypes/data"] == "lx_dtypes/data"


def test_release_helpers_cover_validation_and_main(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(SystemExit, match="Invalid version"):
        release._validate_version("bad-version")

    parser = release.build_parser()
    args = parser.parse_args(["current"])
    assert args.command == "current"


def test_lint_kb_yaml_main_reports_success(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    fake_args = argparse.Namespace(
        paths=[],
        config_paths=[Path("config.yaml")],
        strict_aliases=False,
        strict_mixed_styles=False,
        fail_on_warnings=False,
    )

    monkeypatch.setattr(lint_kb_yaml, "parse_args", lambda: fake_args)
    monkeypatch.setattr(
        lint_kb_yaml,
        "discover_yaml_files",
        lambda *, paths, config_paths: ([Path("a.yaml")], []),
    )
    monkeypatch.setattr(
        lint_kb_yaml,
        "lint_kb_yaml_files",
        lambda yaml_files, strict_aliases, strict_mixed_styles: [],
    )
    monkeypatch.setattr(
        lint_kb_yaml,
        "summarize_issues",
        lambda issues: {"errors": 0, "warnings": 0},
    )

    assert lint_kb_yaml.main() == 0
    assert (
        "Scanned 1 YAML file(s): 0 error(s), 0 warning(s)." in capsys.readouterr().out
    )


def test_lint_kb_yaml_main_fails_when_warnings_requested(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_args = argparse.Namespace(
        paths=[],
        config_paths=[Path("config.yaml")],
        strict_aliases=False,
        strict_mixed_styles=False,
        fail_on_warnings=True,
    )

    monkeypatch.setattr(lint_kb_yaml, "parse_args", lambda: fake_args)
    monkeypatch.setattr(
        lint_kb_yaml,
        "discover_yaml_files",
        lambda *, paths, config_paths: ([Path("a.yaml")], []),
    )
    monkeypatch.setattr(
        lint_kb_yaml,
        "lint_kb_yaml_files",
        lambda yaml_files, strict_aliases, strict_mixed_styles: [],
    )
    monkeypatch.setattr(
        lint_kb_yaml,
        "summarize_issues",
        lambda issues: {"errors": 0, "warnings": 1},
    )

    assert lint_kb_yaml.main() == 1


def test_kb_registry_payload_and_commands(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry_path = tmp_path / "registry.json"
    data_root = tmp_path / "data"
    data_root.mkdir()

    module_dir = data_root / "report_template_examples"
    module_dir.mkdir()
    (module_dir / "config.yaml").write_text(
        "name: report_template_examples\nversion: 0.1.0\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(kb_registry, "resolve_default_data_root", lambda: data_root)

    args = argparse.Namespace(
        registry=registry_path,
        module="report_template_examples",
        version="0.1.0",
        input_dir=[data_root],
    )
    assert kb_registry.cmd_add(args) == 0

    payload = json.loads(registry_path.read_text())
    assert payload["modules"]["report_template_examples"]["0.1.0"]["input_dirs"] == [
        str(data_root.resolve())
    ]

    args_with_medical_field = argparse.Namespace(
        registry=registry_path,
        module="report_template_examples",
        version="0.2.0",
        input_dir=[data_root],
        medical_field="cardiology",
    )
    assert kb_registry.cmd_add(args_with_medical_field) == 0

    payload = json.loads(registry_path.read_text())
    assert (
        payload["modules"]["report_template_examples"]["0.2.0"]["medical_field"]
        == "cardiology"
    )

    show_args = argparse.Namespace(registry=registry_path)
    assert kb_registry.cmd_show(show_args) == 0
    assert '"modules"' in capsys.readouterr().out

    add_current_args = argparse.Namespace(
        registry=registry_path,
        module="report_template_examples",
    )
    assert kb_registry.cmd_add_current(add_current_args) == 0


def test_kb_registry_handles_invalid_registry_payload(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.json"
    registry_path.write_text("[]", encoding="utf-8")

    with pytest.raises(SystemExit, match="Registry payload must be a JSON object."):
        kb_registry._registry_payload(registry_path)
