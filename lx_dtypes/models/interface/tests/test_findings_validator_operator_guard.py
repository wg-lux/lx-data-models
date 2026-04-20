from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml


SCRIPT_PATH = (
    Path(__file__).resolve().parents[4]
    / "scripts"
    / "migrate_findings_validator_operators.py"
)
DATA_ROOT = Path(__file__).resolve().parents[4] / "lx_dtypes" / "data"


def _load_migration_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "migrate_findings_validator_operators_guard",
        SCRIPT_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_repo_yaml_contains_no_legacy_findings_validator_operators() -> None:
    migration = _load_migration_module()
    yaml_files = sorted(DATA_ROOT.rglob("*.yaml")) + sorted(DATA_ROOT.rglob("*.yml"))

    rewrites_by_file: list[str] = []
    for path in yaml_files:
        loaded = _load_yaml(path)
        _, rewrites = migration.rewrite_document(loaded)
        if not rewrites:
            continue
        rendered = ", ".join(
            f"{'.'.join(rewrite.path)}: {rewrite.old!r}->{rewrite.new!r}"
            for rewrite in rewrites
        )
        rewrites_by_file.append(f"{path.relative_to(DATA_ROOT.parent)}: {rendered}")

    assert rewrites_by_file == []
