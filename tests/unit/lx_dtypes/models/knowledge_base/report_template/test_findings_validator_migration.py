from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import yaml

from lx_dtypes.models.knowledge_base.report_template.FindingsValidator import (
    FindingsValidator,
)
from lx_dtypes.models.knowledge_base.report_template.ValidatorRuntime import (
    evaluate_findings_validator_runtime,
)
from tests.paths import REPOSITORY_ROOT

SCRIPT_PATH = REPOSITORY_ROOT / "scripts" / "migrate_findings_validator_operators.py"


def _load_migration_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "migrate_findings_validator_operators",
        SCRIPT_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _semantic_dump(validator: FindingsValidator) -> dict[str, object]:
    dump = validator.model_dump()
    dump.pop("uuid", None)
    dump.pop("created_at", None)
    dump.pop("source_file", None)
    return dump


def test_migration_rewrites_only_findings_validator_operator_fields() -> None:
    migration = _load_migration_module()
    document = [
        {
            "model": "findings_validator",
            "name": "polyp_present",
            "finding": "esophagus_polyp",
            "operator": "present",
            "query": {
                "finding": "esophagus_polyp",
                "operator": "not exists",
            },
        },
        {
            "model": "report_template",
            "name": "t_main",
            "operator": "present",
            "validators": {"findings_validators": ["polyp_present"]},
        },
    ]

    rewritten, rewrites = migration.rewrite_document(document)

    assert [
        (".".join(rewrite.path), rewrite.old, rewrite.new) for rewrite in rewrites
    ] == [
        ("0.operator", "present", "exists"),
        ("0.query.operator", "not exists", "missing"),
    ]
    assert rewritten[0]["operator"] == "exists"
    assert rewritten[0]["query"]["operator"] == "missing"
    assert rewritten[1]["operator"] == "present"


def test_migrated_yaml_round_trip_loads_and_preserves_runtime_behavior(
    tmp_path: Path,
) -> None:
    migration = _load_migration_module()
    migrated_from_legacy = {
        "name": "polyp_present",
        "finding": "esophagus_polyp",
        "operator": "exists",
        "query": {
            "finding": "esophagus_polyp",
            "operator": "exists",
        },
    }
    payload = [{"finding": "esophagus_polyp", "classifications": []}]
    legacy_validator = {
        "name": "polyp_present",
        "finding": "esophagus_polyp",
        "operator": "present",
        "query": {
            "finding": "esophagus_polyp",
            "operator": "present",
        },
    }
    rewritten, rewrites = migration.rewrite_document(legacy_validator)
    assert rewritten == migrated_from_legacy
    assert len(rewrites) == 2

    migrated_path = tmp_path / "findings_validator.yaml"
    migrated_path.write_text(
        yaml.safe_dump(rewritten, sort_keys=False),
        encoding="utf-8",
    )

    migrated_model = FindingsValidator.from_yaml_file(migrated_path)
    canonical_model = FindingsValidator.model_validate(rewritten)
    assert _semantic_dump(migrated_model) == _semantic_dump(canonical_model)
    assert evaluate_findings_validator_runtime(
        canonical_model,
        reported_findings=payload,
    ) == evaluate_findings_validator_runtime(
        migrated_model,
        reported_findings=payload,
    )
