#!/usr/bin/env python3
"""Audit report-template YAML modules for logical integrity issues.

This focuses on "relational glue" checks that static schema validation cannot catch:
- exact string reference integrity
- case/style mismatches (snake_case vs kebab-case vs case variants)
- duplicate name collisions
- circular validator dependencies
- dependency shadowing risks from depends_on modules
- mixed inline/reference finding definitions inside a section
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from textwrap import dedent

import yaml


CANONICAL_ALIAS_MAP: dict[str, str] = {
    "finding_validator": "findings_validator",
}


@dataclass(frozen=True)
class Record:
    module_name: str
    source_file: Path
    model_raw: str
    model: str
    name: str | None
    payload: Mapping[str, Any]


@dataclass(frozen=True)
class Reference:
    feature: str
    source: str
    reference: str
    target_model: str


@dataclass(frozen=True)
class MatrixRow:
    feature: str
    source: str
    reference: str
    definition: str
    status: str
    risk: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        add_help=False,
        description="Audit report-template YAML for logical integrity issues."
        "\n\nChecks include: identifier integrity, dangling references, "
        "style mismatches, collisions, circular validators, and shadowing.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent(
            """
            Examples:
              python scripts/audit_fixture.py \
                --config docs/guides/fixtures/report-template-chaos/config.yaml \
                --data-root lx_dtypes/data

              python scripts/audit_fixture.py --help
            """
        ),
    )
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        help="Show this help message and exit.",
    )
    parser.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Path to module config.yaml to audit.",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("lx_dtypes/data"),
        help="Root directory containing KB module config.yaml files.",
    )
    return parser.parse_args()


def normalize_model_name(model_name: str) -> str:
    return CANONICAL_ALIAS_MAP.get(model_name, model_name)


def normalize_identifier(value: str) -> str:
    """Style-insensitive normalizer for mismatch detection only."""
    return value.strip().lower().replace("-", "_")


def load_yaml_file(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if loaded is None:
        return []
    if isinstance(loaded, list):
        return [item for item in loaded if isinstance(item, dict)]
    if isinstance(loaded, dict):
        return [loaded]
    return []


def iter_yaml_files_from_module_config(
    config_path: Path,
) -> tuple[dict[str, Any], list[Path]]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(config, dict):
        raise ValueError(f"Config is not a mapping: {config_path}")
    config_dir = config_path.parent
    data = config.get("data") or {}
    files: list[Path] = []

    for rel_file in data.get("files") or []:
        file_path = (config_dir / str(rel_file)).resolve()
        if file_path.suffix.lower() in {".yaml", ".yml"}:
            files.append(file_path)

    for rel_dir in data.get("dirs") or []:
        dir_path = (config_dir / str(rel_dir)).resolve()
        if not dir_path.exists():
            continue
        for child in sorted(dir_path.rglob("*.yaml")):
            files.append(child.resolve())
        for child in sorted(dir_path.rglob("*.yml")):
            files.append(child.resolve())

    deduped = []
    seen: set[Path] = set()
    for item in files:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return config, deduped


def load_module_records(config_path: Path) -> tuple[dict[str, Any], list[Record]]:
    config, yaml_files = iter_yaml_files_from_module_config(config_path)
    module_name = str(config.get("name") or config_path.parent.name)
    records: list[Record] = []
    for file_path in yaml_files:
        for item in load_yaml_file(file_path):
            model_raw = str(item.get("model") or "").strip()
            if not model_raw:
                continue
            model = normalize_model_name(model_raw)
            name = item.get("name")
            records.append(
                Record(
                    module_name=module_name,
                    source_file=file_path,
                    model_raw=model_raw,
                    model=model,
                    name=str(name) if isinstance(name, str) else None,
                    payload=item,
                )
            )
    return config, records


def build_name_index(
    records: Iterable[Record],
) -> tuple[dict[str, dict[str, list[Record]]], dict[str, list[Record]]]:
    by_model: dict[str, dict[str, list[Record]]] = {}
    any_name: dict[str, list[Record]] = {}
    for record in records:
        if not record.name:
            continue
        by_model.setdefault(record.model, {}).setdefault(record.name, []).append(record)
        any_name.setdefault(record.name, []).append(record)
    return by_model, any_name


def discover_module_configs(data_root: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    if not data_root.exists():
        return out
    for config_path in sorted(data_root.rglob("config.yaml")):
        config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        resolved = config_path.resolve()
        if isinstance(config, dict) and isinstance(config.get("name"), str):
            out[str(config["name"])] = resolved
        # Fallback: also index by directory name for modules that depend_on by folder key.
        out.setdefault(config_path.parent.name, resolved)
    return out


def extract_references(
    records: Sequence[Record],
) -> tuple[list[Reference], list[str], list[str]]:
    refs: list[Reference] = []
    mixed_inline_sections: list[str] = []
    alias_warnings: list[str] = []

    has_alias = any(rec.model_raw == "finding_validator" for rec in records)
    has_canonical = any(rec.model_raw == "findings_validator" for rec in records)
    if has_alias and has_canonical:
        alias_warnings.append(
            "Module uses both 'finding_validator' alias and canonical 'findings_validator'."
        )
    elif has_alias:
        alias_warnings.append(
            "Module uses alias 'finding_validator' (canonical export model is 'findings_validator')."
        )

    for rec in records:
        if rec.model == "report_template":
            template_name = rec.name or "<unnamed-report-template>"
            for section_ref in rec.payload.get("report_sections") or []:
                if isinstance(section_ref, str):
                    refs.append(
                        Reference(
                            feature="Section Link",
                            source=f"report_template:{template_name}.report_sections",
                            reference=section_ref,
                            target_model="report_template_section",
                        )
                    )

            validators = rec.payload.get("validators") or {}
            for exam_validator in validators.get("examination_validators") or []:
                if isinstance(exam_validator, str):
                    refs.append(
                        Reference(
                            feature="Examination Validator Link",
                            source=f"report_template:{template_name}.validators.examination_validators",
                            reference=exam_validator,
                            target_model="examination_validator",
                        )
                    )
            for finding_validator in validators.get("findings_validators") or []:
                if isinstance(finding_validator, str):
                    refs.append(
                        Reference(
                            feature="Finding Validator Link",
                            source=f"report_template:{template_name}.validators.findings_validators",
                            reference=finding_validator,
                            target_model="findings_validator",
                        )
                    )

        if rec.model == "report_template_section":
            section_name = rec.name or "<unnamed-section>"
            findings = rec.payload.get("findings") or []
            has_string_ref = any(isinstance(item, str) for item in findings)
            has_inline_obj = any(isinstance(item, dict) for item in findings)
            if has_string_ref and has_inline_obj:
                mixed_inline_sections.append(section_name)

            for finding_ref in findings:
                if isinstance(finding_ref, str):
                    refs.append(
                        Reference(
                            feature="Section Finding Link",
                            source=f"report_template_section:{section_name}.findings",
                            reference=finding_ref,
                            target_model="report_finding",
                        )
                    )

        if rec.model == "examination_validator":
            validator_name = rec.name or "<unnamed-examination-validator>"
            for nested in rec.payload.get("examination_validators") or []:
                if isinstance(nested, str):
                    refs.append(
                        Reference(
                            feature="Examination Validator Dependency",
                            source=f"examination_validator:{validator_name}.examination_validators",
                            reference=nested,
                            target_model="examination_validator",
                        )
                    )
            for nested in rec.payload.get("finding_validators") or []:
                if isinstance(nested, str):
                    refs.append(
                        Reference(
                            feature="Examination->Finding Validator Dependency",
                            source=f"examination_validator:{validator_name}.finding_validators",
                            reference=nested,
                            target_model="findings_validator",
                        )
                    )

    return refs, mixed_inline_sections, alias_warnings


def resolve_reference(
    reference: Reference,
    local_by_model: Mapping[str, Mapping[str, Sequence[Record]]],
    dep_by_model: Mapping[str, Mapping[str, Sequence[Record]]],
) -> MatrixRow:
    model = reference.target_model
    local_exact = list(local_by_model.get(model, {}).get(reference.reference, []))
    dep_exact = list(dep_by_model.get(model, {}).get(reference.reference, []))
    exact_matches = local_exact + dep_exact

    if len(exact_matches) == 1:
        match = exact_matches[0]
        definition = f"{match.module_name}:{match.model}:{match.name}"
        return MatrixRow(
            feature=reference.feature,
            source=reference.source,
            reference=reference.reference,
            definition=definition,
            status="PASS",
            risk="Low",
        )

    if len(exact_matches) > 1:
        defs = ", ".join(
            f"{rec.module_name}:{rec.model}:{rec.name}" for rec in exact_matches
        )
        return MatrixRow(
            feature=reference.feature,
            source=reference.source,
            reference=reference.reference,
            definition=defs,
            status="COLLISION",
            risk="Non-deterministic resolution / overwrite risk",
        )

    normalized_ref = normalize_identifier(reference.reference)
    style_matches: list[Record] = []
    for pool in (local_by_model.get(model, {}), dep_by_model.get(model, {})):
        for name, recs in pool.items():
            if normalize_identifier(name) == normalized_ref:
                style_matches.extend(recs)

    if style_matches:
        defs = ", ".join(
            f"{rec.module_name}:{rec.model}:{rec.name}" for rec in style_matches
        )
        return MatrixRow(
            feature=reference.feature,
            source=reference.source,
            reference=reference.reference,
            definition=defs,
            status="STYLE_MISMATCH",
            risk="Exact identifier mismatch (case/separator drift)",
        )

    return MatrixRow(
        feature=reference.feature,
        source=reference.source,
        reference=reference.reference,
        definition="(missing)",
        status="FAIL",
        risk="Dangling reference",
    )


def find_duplicate_names(records: Sequence[Record]) -> list[tuple[str, list[Record]]]:
    by_name: dict[str, list[Record]] = {}
    for rec in records:
        if rec.name:
            by_name.setdefault(rec.name, []).append(rec)
    return [(name, recs) for name, recs in by_name.items() if len(recs) > 1]


def build_validator_graph(records: Sequence[Record]) -> dict[str, list[str]]:
    graph: dict[str, list[str]] = {}
    for rec in records:
        if rec.model != "examination_validator" or not rec.name:
            continue
        refs = rec.payload.get("examination_validators") or []
        graph[rec.name] = [item for item in refs if isinstance(item, str)]
    return graph


def detect_cycles(graph: Mapping[str, Sequence[str]]) -> list[list[str]]:
    cycles: list[list[str]] = []
    state: dict[str, int] = {}
    stack: list[str] = []

    def dfs(node: str) -> None:
        state[node] = 1
        stack.append(node)
        for nxt in graph.get(node, []):
            if nxt not in graph:
                continue
            if state.get(nxt, 0) == 0:
                dfs(nxt)
            elif state.get(nxt) == 1:
                if nxt in stack:
                    start_idx = stack.index(nxt)
                    cycle = stack[start_idx:] + [nxt]
                    if cycle not in cycles:
                        cycles.append(cycle)
        stack.pop()
        state[node] = 2

    for node in graph:
        if state.get(node, 0) == 0:
            dfs(node)
    return cycles


def find_shadowing_risks(
    local_by_model: Mapping[str, Mapping[str, Sequence[Record]]],
    dep_by_model: Mapping[str, Mapping[str, Sequence[Record]]],
) -> list[str]:
    risks: list[str] = []
    for model, local_names in local_by_model.items():
        dep_names = dep_by_model.get(model, {})
        for name in local_names.keys():
            if name in dep_names:
                dep_modules = sorted({rec.module_name for rec in dep_names[name]})
                risks.append(
                    f"{model}:{name} also exists in depends_on module(s): {', '.join(dep_modules)}"
                )
    return risks


def render_traceability_matrix(rows: Sequence[MatrixRow]) -> str:
    lines = [
        "| Feature | Reference (Source) | Definition (Target) | Status | Risk |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        left = f"`{row.reference}` ({row.source})"
        right = (
            row.definition if row.definition == "(missing)" else f"`{row.definition}`"
        )
        lines.append(
            f"| {row.feature} | {left} | {right} | **{row.status}** | {row.risk} |"
        )
    return "\n".join(lines)


def print_section(title: str, items: Sequence[str]) -> None:
    print(f"\n## {title}")
    if not items:
        print("- none")
        return
    for item in items:
        print(f"- {item}")


def main() -> int:
    args = parse_args()
    config_path = args.config.resolve()
    data_root = args.data_root.resolve()

    if not config_path.exists():
        raise SystemExit(f"Config not found: {config_path}")

    config, local_records = load_module_records(config_path)
    module_name = str(config.get("name") or config_path.parent.name)
    local_by_model, _ = build_name_index(local_records)

    module_configs = discover_module_configs(data_root)
    depends_on = [
        str(item) for item in (config.get("depends_on") or []) if isinstance(item, str)
    ]

    dep_records: list[Record] = []
    missing_dep_modules: list[str] = []
    for dep_name in depends_on:
        dep_config_path = module_configs.get(dep_name)
        if not dep_config_path:
            missing_dep_modules.append(dep_name)
            continue
        _, dep_module_records = load_module_records(dep_config_path)
        dep_records.extend(dep_module_records)

    dep_by_model, _ = build_name_index(dep_records)

    refs, mixed_inline_sections, alias_warnings = extract_references(local_records)
    matrix_rows = [
        resolve_reference(ref, local_by_model=local_by_model, dep_by_model=dep_by_model)
        for ref in refs
    ]

    duplicates = find_duplicate_names(local_records)
    dangling = [
        f"{row.feature}: {row.reference} ({row.source})"
        for row in matrix_rows
        if row.status == "FAIL"
    ]
    style_mismatches = [
        f"{row.feature}: {row.reference} -> {row.definition}"
        for row in matrix_rows
        if row.status == "STYLE_MISMATCH"
    ]
    collisions = [
        f"{row.feature}: {row.reference} -> {row.definition}"
        for row in matrix_rows
        if row.status == "COLLISION"
    ]

    validator_graph = build_validator_graph(local_records)
    cycles = detect_cycles(validator_graph)
    cycle_lines = [" -> ".join(cycle) for cycle in cycles]

    duplicate_lines = [
        f"{name}: "
        + ", ".join(f"{rec.model_raw}@{rec.source_file.name}" for rec in recs)
        for name, recs in duplicates
    ]

    shadowing = find_shadowing_risks(
        local_by_model=local_by_model, dep_by_model=dep_by_model
    )

    print(f"# Audit Report: {module_name}")
    print(f"- config: `{config_path}`")
    print(f"- data_root: `{data_root}`")
    print(f"- records_loaded: {len(local_records)}")
    print(f"- depends_on: {depends_on if depends_on else '[]'}")

    print("\n## Traceability Matrix")
    print(render_traceability_matrix(matrix_rows))

    print_section("Dangling References", dangling)
    print_section("Case/Style Mismatches", style_mismatches)
    print_section("Traceability Collisions", collisions)
    print_section(
        "KnowledgeBase Collisions (Duplicate Names in Module)", duplicate_lines
    )
    print_section("Circular Examination Validator Chains", cycle_lines)
    print_section("Shadowing Risks (depends_on overlap)", shadowing)
    print_section("Mixed Inline vs Reference Findings", mixed_inline_sections)
    print_section("Alias Usage Notes", alias_warnings)
    print_section("Missing depends_on Module Configs", missing_dep_modules)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
