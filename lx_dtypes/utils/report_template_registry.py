from __future__ import annotations

from pathlib import Path
from typing import Literal, cast

import yaml

ReportTemplateLifecycleStatusLiteral = Literal["draft", "published"]

GENERATED_DIR_NAME = "generated_templates"
REGISTRY_FILENAME = "report_template_registry.yaml"


def registry_path_for_module(module_dir: Path) -> Path:
    return module_dir / GENERATED_DIR_NAME / REGISTRY_FILENAME


def load_report_template_registry(
    module_dir: Path,
) -> dict[str, ReportTemplateLifecycleStatusLiteral]:
    registry_path = registry_path_for_module(module_dir)
    if not registry_path.exists():
        return {}

    loaded = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        return {}

    templates = loaded.get("templates") or {}
    if not isinstance(templates, dict):
        return {}

    result: dict[str, ReportTemplateLifecycleStatusLiteral] = {}
    for template_name, entry in templates.items():
        if not isinstance(template_name, str) or not template_name.strip():
            continue
        if isinstance(entry, dict):
            lifecycle_status = entry.get("lifecycle_status")
        else:
            lifecycle_status = entry
        if lifecycle_status not in {"draft", "published"}:
            continue
        result[template_name.strip()] = cast(
            ReportTemplateLifecycleStatusLiteral, lifecycle_status
        )
    return result


def write_report_template_registry(
    module_dir: Path,
    statuses: dict[str, ReportTemplateLifecycleStatusLiteral],
) -> Path:
    registry_path = registry_path_for_module(module_dir)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "templates": {
            template_name: {"lifecycle_status": lifecycle_status}
            for template_name, lifecycle_status in sorted(statuses.items())
        }
    }
    registry_path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return registry_path


def set_report_template_lifecycle_status(
    module_dir: Path,
    template_name: str,
    lifecycle_status: ReportTemplateLifecycleStatusLiteral,
) -> Path:
    statuses = load_report_template_registry(module_dir)
    statuses[template_name.strip()] = lifecycle_status
    return write_report_template_registry(module_dir, statuses)
