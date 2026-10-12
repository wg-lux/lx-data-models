"""Reconcile the pinned MST 3.0 workbook with the existing package identifiers.

Run with ``uv run --with xlrd python scripts/import_mst_excel.py --check``.
The mapping specification is deliberately separate from the generated KB records.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
import tempfile
from typing import Literal

from pydantic import BaseModel, ConfigDict, JsonValue, TypeAdapter
import yaml

ROOT = Path(__file__).resolve().parents[1]
TERMINOLOGY = Path("lx_dtypes/data/terminology/mst_3_0_terminology")
REPORTING = Path("lx_dtypes/data/report_templates/mst_3_0")
GENERATED = TERMINOLOGY / "data/82_excel_attributes.yml"
Record = dict[str, JsonValue]
RECORDS = TypeAdapter(list[Record])


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Binding(StrictModel):
    label: str
    name: str


class ModifierScope(StrictModel):
    sheet: Literal["Anatomy", "EUSanatomy"]
    first: int
    last: int
    site_first: int
    site_last: int


class ImportSpec(StrictModel):
    schema_version: Literal["1"]
    source_sha256: str
    version: Literal["3.0.0"]
    bindings: dict[str, dict[str, Binding]]
    numeric_values: dict[str, str]
    text_values: list[str]
    classification_values: dict[str, str]
    decisions: list[str]
    modifier_scopes: list[ModifierScope]


class Workbook(StrictModel):
    source_sha256: str
    sheets: dict[str, list[list[str]]]

    def cell(self, sheet: str, row: int, column: int) -> str:
        return self.sheets[sheet][row - 1][column - 1].strip()

    def values(self, sheet: str, start: int, end: int, column: int) -> list[Value]:
        return [
            Value(self.cell(sheet, row, column), reference(sheet, row, column))
            for row in range(start, end + 1)
            if self.cell(sheet, row, column)
        ]


@dataclass(frozen=True)
class Value:
    label: str
    source: str


def reference(sheet: str, row: int, column: int) -> str:
    return f"'{sheet}'!{chr(64 + column)}{row}"


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def strings(record: Record, key: str) -> list[str]:
    value = record.get(key, [])
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise ValueError(f"{record.get('name')}: {key} must be a string list")
    return [v for v in value if isinstance(v, str)]


def text(record: Record, key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{record.get('name')}: {key} must be a string")
    return value


def dump(value: object) -> str:
    return yaml.safe_dump(
        value, allow_unicode=True, sort_keys=False, default_flow_style=None, width=110
    )


def render_records(path: Path, records: list[Record]) -> str:
    """Keep comments and formatting of records that the import does not change."""
    original = path.read_text()
    before = RECORDS.validate_python(yaml.safe_load(original))
    nodes = yaml.compose(original)
    if not isinstance(nodes, yaml.SequenceNode) or len(before) != len(records):
        raise ValueError(f"{path}: baseline record layout changed")
    lines = original.splitlines(keepends=True)
    for old, new, node in reversed(
        list(zip(before, records, nodes.value, strict=True))
    ):
        if old != new:
            end = node.end_mark.line + int(node.end_mark.column > 0)
            lines[node.start_mark.line : end] = [dump([new])]
    return "".join(lines)


def read_workbook(path: Path, spec: ImportSpec) -> Workbook:
    digest = sha256(path.read_bytes()).hexdigest()
    if digest != spec.source_sha256:
        raise ValueError(
            "Workbook SHA-256 differs from the reviewed import specification"
        )
    import xlrd  # Optional authoring dependency; never needed to load the KB.

    book = xlrd.open_workbook(str(path))
    sheets: dict[str, list[list[str]]] = {}
    for sheet in book.sheets():
        rows: list[list[str]] = []
        for row in range(sheet.nrows):
            cells: list[str] = []
            for column in range(sheet.ncols):
                value = sheet.cell_value(row, column)
                if not isinstance(value, str):
                    raise ValueError(
                        f"{reference(sheet.name, row + 1, column + 1)}: expected text"
                    )
                cells.append(value)
            rows.append(cells)
        sheets[sheet.name] = rows
    result = Workbook(source_sha256=digest, sheets=sheets)
    for sheet, bindings in spec.bindings.items():
        for cell, binding in bindings.items():
            actual = result.cell(sheet, int(cell[1:]), ord(cell[0]) - 64)
            if actual != binding.label.strip():
                raise ValueError(
                    f"{sheet}!{cell}: expected {binding.label!r}, found {actual!r}"
                )
    return result


class Importer:
    def __init__(self, root: Path, workbook: Workbook, spec: ImportSpec):
        self.root, self.workbook, self.spec = root, workbook, spec
        self.files = {
            p.relative_to(root): RECORDS.validate_python(yaml.safe_load(p.read_text()))
            for p in sorted((root / TERMINOLOGY / "data").glob("*.yaml"))
        }
        self.records: dict[str, Record] = {}
        for rows in self.files.values():
            for row in rows:
                name = text(row, "name")
                if name in self.records:
                    raise ValueError(f"Duplicate baseline identity: {name}")
                self.records[name] = row
        self.generated: dict[str, Record] = {}
        self.attributes: dict[str, dict[str, list[Value]]] = defaultdict(dict)
        self.links: dict[str, list[str]] = defaultdict(list)
        self.locations: dict[str, list[str]] = {}
        self.procedures: dict[str, str] = {}
        self.provenance: dict[str, list[str]] = {}
        self.choice_cache: dict[tuple[str, str, bool], str] = {}
        self.attribute_cache: dict[tuple[str, tuple[str, ...]], list[str]] = {}

    def add(
        self, model: str, name: str, label: str, source: str, **fields: JsonValue
    ) -> str:
        row: Record = {
            "model": model,
            "name": name,
            "name_en": label,
            "name_de": label,
            "description": f"MST 3.0 Excel: {source}.",
            **fields,
        }
        # Existing translated choices can be reused by callers; never relabel them silently.
        if name in self.records:
            raise ValueError(f"Generated identity collides with baseline: {name}")
        if name in self.generated and self.generated[name] != row:
            raise ValueError(f"Conflicting generated definition: {name}")
        self.generated[name] = row
        return name

    def owner(self, sheet: str, row: int, column: int) -> str | None:
        binding = self.spec.bindings.get(sheet, {}).get(f"{chr(64 + column)}{row}")
        return binding.name if binding else None

    def table(
        self,
        sheet: str,
        start: int,
        end: int,
        owner_col: int,
        attr_col: int,
        value_col: int,
    ) -> None:
        owner, attribute = None, ""
        for row in range(start, end + 1):
            bound = self.owner(sheet, row, owner_col)
            if self.workbook.cell(sheet, row, owner_col) and bound is None:
                raise ValueError(f"{sheet}:{row}: unmapped term")
            if bound:
                owner, attribute = bound, ""
            label = self.workbook.cell(sheet, row, attr_col)
            if label:
                attribute = label
                if owner is None:
                    raise ValueError(f"{sheet}:{row}: attribute without owner")
                self.attributes[owner].setdefault(attribute, [])
            value = self.workbook.cell(sheet, row, value_col)
            if value and owner and attribute:
                self.attributes[owner][attribute].append(
                    Value(value, reference(sheet, row, value_col))
                )

    def collect_attributes(self) -> None:
        for args in [
            ("Luminal_findings", 5, 165, 2, 3, 4),
            ("ERCP findings", 5, 29, 1, 3, 4),
            ("ERCP findings", 30, 82, 2, 3, 4),
            ("Procedures", 4, 102, 1, 2, 3),
            ("Procedures", 106, 161, 1, 2, 3),
            ("Procedures", 165, 187, 1, 2, 3),
            ("Adv events", 6, 33, 1, 2, 3),
            ("Adv events", 38, 65, 1, 2, 3),
        ]:
            self.table(*args)
        # In the printed table these two value columns span several finding rows.
        for start, end in [(46, 53), (60, 65)]:
            values = self.workbook.values("Luminal_findings", start, start + 2, 4)
            for row in range(start, end + 1):
                owner = self.owner("Luminal_findings", row, 2)
                if owner:
                    self.attributes[owner]["Distribution"] = values
        self.attributes["mst_excavated_ulcer"]["Number"] = [
            Value("#", "'Luminal_findings'!C148 (unspecified numeric number)")
        ]
        # Source discrepancy is explicit: None occurs only in the organ matrix.
        self.attributes["mst_ercp_papillary_features"]["Output"].insert(
            0, Value("None", "'ERCP_findings_organ'!B11")
        )
        for owner in [
            "mst_event_intraprocedure_cardiopulmonary",
            "mst_event_intraprocedure_allergic_reaction",
        ]:
            values = self.attributes[owner]["Action"]
            self.attributes[owner]["Action"] = [
                v for v in values if v.label != "list below"
            ] + self.workbook.values("Adv events", 71, 78, 3)
        self.attributes["mst_proc_eus_fna"]["Volume"] = [
            Value("ml", "'Procedures'!C167"),
            Value("N/A", "'Procedures'!C167"),
        ]
        self.attributes["mst_proc_luminal_polypectomy"]["Pre-injection"] = [
            Value("Yes", "'Procedures'!C44"),
            Value("No", "'Procedures'!C44"),
        ]
        self.attributes["mst_proc_luminal_transmural_drainage"]["EUS guidance"] = [
            Value("Yes", "'Procedures'!C94"),
            Value("No", "'Procedures'!C94"),
        ]
        for start, end, disease in [
            (5, 16, False),
            (18, 44, True),
            (48, 57, False),
            (59, 74, True),
            (80, 84, False),
            (86, 94, True),
            (99, 101, False),
            (103, 131, True),
            (136, 140, False),
            (141, 166, True),
        ]:
            for row in range(start, end + 1):
                owner = self.owner("Reasons", row, 2)
                if owner:
                    if disease:
                        self.attributes[owner]["Qualifier"] = self.workbook.values(
                            "Reasons", start, start + (6 if start == 141 else 5), 3
                        )
                    else:
                        for qualifier in self.workbook.values(
                            "Reasons", start, start + 1, 3
                        ):
                            self.attributes[owner][qualifier.label] = [
                                Value("Specify", qualifier.source)
                            ]
        self.eus_attributes()

    def anatomy_modifiers(self) -> None:
        # Values printed down a column apply to a block of sites, not just the
        # adjacent row. The two biliary sub-blocks are intentionally narrower.
        scopes = self.spec.modifier_scopes
        self.add(
            "unit",
            "mst_excel_minute",
            "Minute",
            "Anatomy time modifiers",
            abbreviation="min",
        )
        descriptors: dict[str, list[str]] = defaultdict(list)
        for scope in scopes:
            sheet, first, last = scope.sheet, scope.first, scope.last
            site_first, site_last = scope.site_first, scope.site_last
            categorical: list[str] = []
            fields: list[str] = []
            for value in self.workbook.values(sheet, first, last, 3):
                unit = (
                    "mst_centimeter"
                    if "xx cm" in value.label
                    else "mst_millimeter"
                    if "xx mm" in value.label
                    else "mst_excel_minute"
                    if "xx min" in value.label
                    else "mst_count"
                    if value.label == "station no"
                    else None
                )
                if unit or "specify" in value.label:
                    name = "mst_excel_modifier_" + slug(value.label)
                    if name not in self.generated:
                        fields_dict: Record = {
                            "classification_choice_descriptor_type": "numeric"
                            if unit
                            else "text"
                        }
                        if unit:
                            fields_dict.update(unit=unit, numeric_min=0)
                        self.add(
                            "classification_choice_descriptor",
                            name,
                            value.label,
                            value.source,
                            **fields_dict,
                        )
                    fields.append(name)
                else:
                    categorical.append(value.label)
            if categorical:
                name = f"mst_excel_modifier_{slug(sheet)}_{first}"
                self.add(
                    "classification_choice_descriptor",
                    name,
                    "Location modifier",
                    f"'{sheet}'!C{first}:C{last}",
                    classification_choice_descriptor_type="selection",
                    selection_options=list(categorical),
                    selection_multiple=True,
                    selection_multiple_n_max=len(categorical),
                )
                fields.append(name)
            for row in range(site_first, site_last + 1):
                owner = self.owner(sheet, row, 2)
                if owner:
                    descriptors[owner].extend(fields)
        for owner, names in descriptors.items():
            self.records[owner]["classification_choice_descriptors"] = list(
                dict.fromkeys(names)
            )

    def eus_attributes(self) -> None:
        w = self.workbook
        lists = {
            "Origin": w.values("EUS findings", 29, 29, 3),
            "Layer origin": w.values("EUS findings", 29, 32, 4),
            "Outer limit": w.values("EUS findings", 29, 36, 5),
            "size (mm)": [Value("mm", "'EUS findings'!F3")],
            "shape/character": w.values("EUS findings", 65, 82, 2),
            "Margins": w.values("EUS findings", 65, 73, 3),
            "Echofeatures": w.values("EUS findings", 65, 78, 4),
            "Cyst features": w.values("EUS findings", 65, 81, 5),
            "Invasion ext": w.values("EUS findings", 112, 117, 2),
            "invasion into": w.values("EUS findings", 112, 112, 3),
            "T-stage": [Value("Specify", "'EUS findings'!D86")],
            "N-stage": [Value("Specify", "'EUS findings'!E86")],
            "degree": w.values("EUS findings", 112, 116, 6),
            "number": [Value("#", "'EUS findings'!G86")],
            "duct changes": w.values("EUS findings", 112, 119, 8),
        }
        for header, start, end in [(3, 4, 26), (39, 40, 62), (86, 87, 109)]:
            for row in range(start, end + 1):
                owner = self.owner("EUS findings", row - start + 4, 1)
                if owner is None:
                    raise ValueError(f"Missing EUS binding at row {row}")
                for col in range(2, len(w.sheets["EUS findings"][header - 1]) + 1):
                    if w.cell("EUS findings", row, col).lower() != "x":
                        continue
                    attr = w.cell("EUS findings", header, col)
                    if attr != "location":
                        self.attributes[owner][attr] = list(lists[attr])
        specific: dict[tuple[str, str], list[Value]] = defaultdict(list)
        for header, start, end, attr in [
            (3, 4, 14, "shape/character"),
            (16, 17, 27, "shape/character"),
            (29, 30, 37, "Echofeatures"),
            (40, 41, 48, "Echofeatures"),
        ]:
            sheet = "EUS findings_attribute lists"
            for row in range(start, end + 1):
                owner = self.owner(sheet, row, 1)
                if owner is None:
                    raise ValueError(f"Missing EUS attribute binding: {row}")
                for col in range(2, 12):
                    if w.cell(sheet, row, col).lower() == "x":
                        label = w.cell(sheet, header, col)
                        specific[(owner, attr)].append(
                            Value(label, reference(sheet, row, col))
                        )
        for (owner, attr), values in specific.items():
            self.attributes[owner][attr] = values

    def attribute(self, owner: str, label: str, values: list[Value]) -> list[str]:
        if not values:
            raise ValueError(f"{owner}/{label}: no explicit values")
        sources = list(dict.fromkeys(v.source for v in values))
        name = f"{owner}_{slug(label)}"
        self.provenance[name] = sources
        if [v.label for v in values] == ["main sites"]:
            choices = [
                choice
                for r in self.records.values()
                if text(r, "model") == "classification"
                and text(r, "name").startswith("mst_location_")
                for choice in strings(r, "classification_choices")
            ]
            self.add(
                "classification",
                name,
                label,
                ", ".join(sources),
                classification_types=["mst_location"],
                classification_choices=list(choices),
            )
            return [name]
        cache_key = (slug(label), tuple(v.label.lower() for v in values))
        if cache_key in self.attribute_cache:
            return self.attribute_cache[cache_key]
        references = [
            self.spec.classification_values[v.label]
            for v in values
            if v.label in self.spec.classification_values
        ]
        if references:
            if len(references) != len(values):
                raise ValueError(
                    f"{name}: mixes classification references and literal values"
                )
            return list(dict.fromkeys(references))
        choices: list[str] = []
        for value in values:
            unit = next(
                (
                    u
                    for key, u in self.spec.numeric_values.items()
                    if key.lower() == value.label.lower()
                ),
                None,
            )
            is_text = value.label.lower() in {v.lower() for v in self.spec.text_values}
            key = (value.label.lower(), unit or "", is_text)
            if key in self.choice_cache:
                choices.append(self.choice_cache[key])
                continue
            digest = sha256(json.dumps(key).encode()).hexdigest()[:8]
            choice = f"mst_excel_{slug(value.label) or 'value'}_{digest}"
            descriptors: list[str] = []
            if unit or is_text:
                descriptor = (
                    f"mst_excel_numeric_{unit}" if unit else "mst_free_text_value"
                )
                if unit and descriptor not in self.generated:
                    self.add(
                        "classification_choice_descriptor",
                        descriptor,
                        "Value",
                        "numeric workbook field",
                        classification_choice_descriptor_type="numeric",
                        unit=unit,
                        numeric_min=0,
                    )
                descriptors.append(descriptor)
            self.add(
                "classification_choice",
                choice,
                value.label,
                value.source,
                classification_choice_descriptors=list(descriptors),
            )
            self.choice_cache[key] = choice
            choices.append(choice)
        self.add(
            "classification",
            name,
            label,
            ", ".join(sources),
            classification_types=["mst_attribute"],
            classification_choices=list(choices),
        )
        self.attribute_cache[cache_key] = [name]
        return [name]

    def location_matrix(
        self, sheet: str, start: int, end: int, term_col: int, groups: list[list[str]]
    ) -> None:
        for row in range(start, end + 1):
            owner = self.owner(sheet, row, term_col)
            if owner is None:
                continue
            choices = [
                n
                for offset, group in enumerate(groups, term_col + 1)
                if self.workbook.cell(sheet, row, offset).lower() == "x"
                for classification in group
                for n in strings(self.records[classification], "classification_choices")
            ]
            if choices:
                self.locations[owner] = list(dict.fromkeys(choices))

    def collect_locations(self) -> None:
        luminal = [
            [f"mst_location_{s}"]
            for s in ["esophagus", "stomach", "duodenum", "jejunum", "ileum", "colon"]
        ]
        self.location_matrix("Luminal_findings_organ", 6, 70, 2, luminal)
        ercp = [[], [], ["mst_location_biliary_tree"], ["mst_location_pancreatic_duct"]]
        # Actual legacy identifiers are checked instead of inferred from display labels.
        self.location_matrix("ERCP_findings_organ", 30, 48, 2, ercp)
        eus = [
            [f"mst_eus_location_{s}"]
            for s in [
                "esophagus",
                "stomach",
                "duodenum",
                "pancreas",
                "biliary_tract",
                "colorectum",
            ]
        ]
        self.location_matrix("EUS findings_organ", 4, 28, 1, eus)
        self.locations["mst_ercp_papillary_features"] = [
            "mst_duodenum_major_papilla",
            "mst_duodenum_minor_papilla",
        ]
        for owner, choices in self.locations.items():
            name = f"{owner}_anatomical_location"
            self.add(
                "classification",
                name,
                "Location",
                "organ applicability matrix",
                classification_types=["mst_location"],
                classification_choices=list(choices),
            )
            self.links[owner].append(name)

    def severity(self) -> None:
        sheet = "Adv event severity"
        choices = []
        for col in range(2, 7):
            label = self.workbook.cell(sheet, 3, col)
            name = f"mst_event_severity_{slug(label)}"
            outcomes = [
                self.workbook.cell(sheet, row, 1)
                for row in range(5, 18)
                if self.workbook.cell(sheet, row, col).lower() == "x"
            ]
            self.add(
                "classification_choice",
                name,
                label,
                f"{reference(sheet, 3, col)}; outcomes: " + "; ".join(outcomes),
            )
            choices.append(name)
        self.add(
            "classification",
            "mst_event_severity",
            "Adverse event severity",
            "'Adv event severity'!B3:F17; no inferred hospitalization thresholds",
            classification_types=["mst_attribute"],
            classification_choices=list(choices),
        )
        for record in self.records.values():
            if text(record, "model") == "finding" and "mst_adverse_event" in strings(
                record, "finding_types"
            ):
                self.links[text(record, "name")].extend(
                    ["mst_event_severity", "mst_event_outcome"]
                )

    def compile(self) -> dict[Path, str]:
        self.collect_attributes()
        self.anatomy_modifiers()
        self.collect_locations()
        self.severity()
        self.add(
            "classification",
            "mst_excel_paris_type_0_4",
            "Paris type 0-4",
            "'Luminal_findings'!D110",
            classification_types=["mst_standard_classification"],
            classification_choices=[f"mst_paris_{i}" for i in range(5)],
        )
        for owner, attributes in self.attributes.items():
            record = self.records[owner]
            target = owner
            if text(record, "model") == "intervention":
                target = owner + "_details"
                self.procedures[owner] = target
                self.add(
                    "finding",
                    target,
                    text(record, "name_en") + " details",
                    "Procedures",
                    finding_types=[
                        "mst_luminal_finding"
                        if "_luminal_" in owner
                        else "mst_ercp_finding"
                        if "_ercp_" in owner
                        else "mst_eus_finding"
                    ],
                    interventions=[owner],
                )
            for label, values in attributes.items():
                self.links[target].extend(self.attribute(target, label, values))
        for owner, links in self.links.items():
            record = self.records.get(owner, self.generated.get(owner))
            if record is None:
                raise ValueError(f"Unknown attribute owner: {owner}")
            record["classifications"] = list(dict.fromkeys(links))
        # Both C and M are distances, not categorical selections without a value.
        for name in ["mst_prague_c", "mst_prague_m"]:
            self.records[name]["classification_choice_descriptors"] = [
                "mst_length_cm_value"
            ]
        reports_path = REPORTING / "report_templates.yml"
        reports = RECORDS.validate_python(
            yaml.safe_load((self.root / reports_path).read_text())
        )
        self.update_reports(reports)
        outputs = {
            path: render_records(self.root / path, rows)
            for path, rows in self.files.items()
        }
        outputs[GENERATED] = (
            "# Generated by scripts/import_mst_excel.py; do not edit.\n"
            + dump(list(self.generated.values()))
        )
        outputs[reports_path] = render_records(self.root / reports_path, reports)
        outputs[TERMINOLOGY / "excel_source.yml"] = dump(
            {
                "owner": "lx-dtypes maintainers",
                "source_sha256": self.workbook.source_sha256,
                "decisions": self.spec.decisions,
                "attribute_sources": self.provenance,
                "sheets": self.workbook.sheets,
            }
        )
        return outputs

    def update_reports(self, reports: list[Record]) -> None:
        reusable = {
            text(r, "name"): r for r in reports if text(r, "model") == "report_finding"
        }
        for record in reports:
            if text(record, "model") != "report_template_section":
                continue
            findings = record.get("findings", [])
            if not isinstance(findings, list):
                raise ValueError("Report findings must be a list")
            for index, finding in enumerate(findings):
                if isinstance(finding, str):
                    if finding in reusable:
                        finding = {
                            k: v
                            for k, v in reusable[finding].items()
                            if k
                            not in {
                                "model",
                                "name",
                                "name_de",
                                "name_en",
                                "description",
                            }
                        }
                    else:
                        finding = {
                            "finding": finding,
                            "required": False,
                            "multiple_allowed": True,
                        }
                    findings[index] = finding
                if not isinstance(finding, dict):
                    raise ValueError("Report findings must be explicit mappings")
                owner = text(finding, "finding")
                if owner in self.links:
                    requirements: list[JsonValue] = [
                        {"classification": name, "required": False}
                        for name in self.report_links(owner, text(record, "name"))
                    ]
                    finding["classifications"] = requirements
            section = text(record, "name")
            if "procedures_events" in section:
                family = (
                    "ercp"
                    if "ercp" in section
                    else "eus"
                    if "eus" in section
                    else "luminal"
                )
                existing = {text(f, "finding") for f in findings if isinstance(f, dict)}
                for intervention, owner in self.procedures.items():
                    if f"_{family}_" in intervention and owner not in existing:
                        findings.append(
                            {
                                "finding": owner,
                                "required": False,
                                "multiple_allowed": True,
                                "classifications": [
                                    {"classification": name, "required": False}
                                    for name in self.links[owner]
                                ],
                            }
                        )
                # A report finding must also be in the examination vocabulary.
                for examination in self.records.values():
                    if text(examination, "model") == "examination":
                        members = strings(examination, "findings")
                        if f"mst_{family}_procedure_summary" in members:
                            examination["findings"] = list(
                                dict.fromkeys(
                                    members
                                    + [
                                        n
                                        for i, n in self.procedures.items()
                                        if f"_{family}_" in i
                                    ]
                                )
                            )

    def report_links(self, owner: str, section: str) -> list[str]:
        """Intersect finding locations with the workbook's procedure/organ matrix."""
        family = section.split("_")[1]
        if family == "eus":  # The workbook has no EUS column in proc_organ.
            return self.links[owner]
        column = {"egd": 2, "enteroscopy": 3, "vce": 4, "colonoscopy": 5, "ercp": 6}[
            family
        ]
        groups = [
            "esophagus",
            "stomach",
            "duodenum",
            "jejunum",
            "ileum",
            "colon",
            "biliary_tree",
            "pancreatic_duct",
        ]
        allowed = {
            choice
            for row, group in enumerate(groups, 4)
            if self.workbook.cell("proc_organ", row, column).lower() == "x"
            for choice in strings(
                self.records[f"mst_location_{group}"], "classification_choices"
            )
        }
        result: list[str] = []
        for name in self.links[owner]:
            record = self.generated.get(name, self.records.get(name))
            if record is None:
                raise ValueError(f"Missing classification: {name}")
            if "mst_location" not in strings(record, "classification_types"):
                result.append(name)
                continue
            original = strings(record, "classification_choices")
            choices = [n for n in original if n in allowed]
            if not choices:
                raise ValueError(
                    f"{section}: {owner} has no applicable anatomical site"
                )
            if choices == original:
                result.append(name)
                continue
            digest = sha256(json.dumps(choices).encode()).hexdigest()[:8]
            scoped = f"mst_excel_{family}_location_{digest}"
            if scoped not in self.generated:
                self.add(
                    "classification",
                    scoped,
                    "Location",
                    f"'proc_organ'!{chr(64 + column)}4:{chr(64 + column)}11 intersected with finding/organ matrix",
                    classification_types=["mst_location"],
                    classification_choices=list(choices),
                )
            result.append(scoped)
        return result


def render(root: Path, workbook: Path, spec_path: Path) -> dict[Path, str]:
    spec = ImportSpec.model_validate(yaml.safe_load(spec_path.read_text()))
    return Importer(root, read_workbook(workbook, spec), spec).compile()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=ROOT / "mst30_tables(1).xls")
    parser.add_argument("--spec", type=Path, default=ROOT / "scripts/mst/import.yml")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = render(ROOT, args.workbook, args.spec)
    # Validate the complete generated dependency closure before changing any source file.
    from lx_dtypes.models.interface.DataLoader import DataLoader
    from lx_dtypes.knowledge_bases import (
        PackagedKnowledgeBaseCatalog,
        knowledge_base_content_sha256,
    )

    with tempfile.TemporaryDirectory(prefix="mst-import-") as directory:
        stage = Path(directory)
        for relative, content in outputs.items():
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        for module in [TERMINOLOGY, REPORTING]:
            (stage / module / "config.yaml").write_bytes(
                (ROOT / module / "config.yaml").read_bytes()
            )
        kb = DataLoader(input_dirs=[stage / "lx_dtypes/data"]).load_knowledge_base(
            "mst_3_0"
        )
        kb.export_core_concepts()
        for template in kb.report_template:
            kb.export_report_template(template)
        catalog_path = Path("lx_dtypes/data/catalog.json")
        catalog = PackagedKnowledgeBaseCatalog.model_validate_json(
            (ROOT / catalog_path).read_text()
        )
        entries = []
        for entry in catalog.knowledge_bases:
            for module in [TERMINOLOGY, REPORTING]:
                if entry.module_name == module.name and entry.version == "3.0.0":
                    entry = entry.model_copy(
                        update={
                            "content_sha256": knowledge_base_content_sha256(
                                stage / module
                            )
                        }
                    )
            entries.append(entry)
        catalog = catalog.model_copy(update={"knowledge_bases": tuple(entries)})
        outputs[catalog_path] = (
            json.dumps(catalog.model_dump(mode="json", exclude_unset=True), indent=2)
            + "\n"
        )
    changed = [
        p
        for p, content in outputs.items()
        if not (ROOT / p).exists() or (ROOT / p).read_text() != content
    ]
    if args.check:
        for path in changed:
            print(f"Stale generated content: {path}")
        return int(bool(changed))
    for path in changed:
        (ROOT / path).write_text(outputs[path])
    print(
        f"Reconciled MST 3.0: {len(changed)} files updated; all templates exported successfully."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
