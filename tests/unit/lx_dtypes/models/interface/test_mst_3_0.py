"""Verify that the complete MST 3.0 data survives terminology merges."""

from pathlib import Path

import pytest

from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.interface.KnowledgeBaseResolver import load_knowledge_base

ROOT = Path(__file__).resolve().parents[5]


@pytest.fixture(scope="module")
def mst_3_0() -> KnowledgeBase:
    return load_knowledge_base(
        "mst_3_0",
        version="3.0.0",
        input_dirs=[ROOT / "lx_dtypes/data"],
    )


def test_mst_3_0_loads(mst_3_0: KnowledgeBase) -> None:
    assert mst_3_0.config.name == "mst_3_0"
    assert mst_3_0.config.version == "3.0.0"
    mst_3_0.export_core_concepts()


def test_mst_3_0_has_complete_data(mst_3_0: KnowledgeBase) -> None:
    assert len(mst_3_0.finding) == 389
    assert len(mst_3_0.classification) == 293
    assert len(mst_3_0.classification_choice) == 546


def test_mst_anatomy_location_exists(mst_3_0: KnowledgeBase) -> None:
    assert "mst_location_esophagus" in mst_3_0.classification
    assert "mst_location_colon" in mst_3_0.classification
    assert "mst_eus_other" in mst_3_0.finding


def _classification(kb: KnowledgeBase, finding: str, label: str):
    matches = [
        kb.classification[name]
        for name in kb.finding[finding].classifications
        if kb.classification[name].name_en.casefold() == label.casefold()
    ]
    assert len(matches) == 1, (finding, label, [item.name for item in matches])
    return matches[0]


def _labels(kb: KnowledgeBase, finding: str, attribute: str) -> set[str]:
    classification = _classification(kb, finding, attribute)
    return {
        kb.classification_choice[name].name_en.casefold()
        for name in classification.classification_choices
    }


def test_excel_finding_specific_values(mst_3_0: KnowledgeBase) -> None:
    assert _labels(mst_3_0, "mst_protruding_polyp", "Appearance") == {
        "malignant",
        "adenomatous",
        "hyperplastic",
        "inflammatory",
        "pseudopolyp",
    }
    assert _labels(mst_3_0, "mst_protruding_polyp", "Shape") == {
        "pedunculated",
        "semipedunculated",
        "sessile",
        "flat elevated",
    }
    assert _labels(mst_3_0, "mst_protruding_polyp", "Bleeding") == {
        "yes",
        "stigmata",
        "no",
    }
    assert _labels(mst_3_0, "mst_flat_dieulafoy_lesion", "Bleeding") == {
        "spurting",
        "oozing",
        "clot",
        "no",
    }
    assert _labels(mst_3_0, "mst_luminal_compression", "size") == {"small", "large"}
    assert _labels(mst_3_0, "mst_luminal_stenosis", "Traversable") == {
        "yes",
        "after dilation",
        "no",
    }
    assert _labels(mst_3_0, "mst_ercp_tumor", "Obstructing") == {
        "yes",
        "partially",
        "no",
    }


def test_eus_lesion_specific_lists(mst_3_0: KnowledgeBase) -> None:
    # EUS findings_attribute lists, rows 6/19 and 33/44; not the union of every lesion.
    assert _labels(mst_3_0, "mst_eus_mass", "shape/character") == {
        "round",
        "oval",
        "triangular",
        "linear",
        "lobulated",
        "sessile",
        "ulcerated",
        "irregular",
        "circumferential",
        "number",
    }
    assert _labels(mst_3_0, "mst_eus_mass", "Echofeatures") == {
        "hypoechoic",
        "isoechoic",
        "hyperechoic",
        "homogeneous",
        "heterogeneous",
        "cystic components",
        "solid",
        "shadowing",
        "distal enhancement",
    }
    assert _labels(mst_3_0, "mst_eus_varices", "shape/character") == {
        "tortuous",
        "tubular",
    }
    for field in [
        "Origin",
        "Layer origin",
        "Outer limit",
        "Margins",
        "Invasion ext",
        "invasion into",
        "T-stage",
        "N-stage",
    ]:
        _classification(mst_3_0, "mst_eus_mass", field)


def test_location_matrix_does_not_offer_unmarked_organs(mst_3_0: KnowledgeBase) -> None:
    assert set(
        _classification(
            mst_3_0, "mst_luminal_ring_web", "Location"
        ).classification_choices
    ) == set(mst_3_0.classification["mst_location_esophagus"].classification_choices)
    assert set(
        _classification(mst_3_0, "mst_eus_varices", "Location").classification_choices
    ) == (
        set(mst_3_0.classification["mst_eus_location_esophagus"].classification_choices)
        | set(mst_3_0.classification["mst_eus_location_stomach"].classification_choices)
    )
    assert set(
        _classification(
            mst_3_0, "mst_ercp_pancreas_divisum", "Location"
        ).classification_choices
    ) == set(
        mst_3_0.classification["mst_location_pancreatic_duct"].classification_choices
    )


def test_measurements_have_descriptor_inputs(mst_3_0: KnowledgeBase) -> None:
    for name in ["mst_prague_c", "mst_prague_m"]:
        descriptors = mst_3_0.classification_choice[
            name
        ].classification_choice_descriptors
        assert len(descriptors) == 1
        descriptor = mst_3_0.classification_choice_descriptor[descriptors[0]]
        assert descriptor.is_numeric
        assert descriptor.unit == "mst_centimeter"
    site = mst_3_0.classification_choice["mst_jejunum_jejunum"]
    modifiers = [
        mst_3_0.classification_choice_descriptor[name]
        for name in site.classification_choice_descriptors
    ]
    assert any(d.is_numeric and d.unit == "mst_excel_minute" for d in modifiers)
    assert any(d.is_numeric and d.unit == "mst_centimeter" for d in modifiers)
    assert all(
        not d.classification_choice_descriptors
        for d in [
            mst_3_0.classification_choice[n]
            for n in _classification(
                mst_3_0, "mst_luminal_compression", "size"
            ).classification_choices
        ]
    )


def test_procedure_details_preserve_distinct_results(mst_3_0: KnowledgeBase) -> None:
    for method in ["emr", "esd"]:
        finding = f"mst_proc_luminal_{method}_details"
        assert mst_3_0.finding[finding].interventions == [f"mst_proc_luminal_{method}"]
        assert _labels(mst_3_0, finding, "Result") == {
            "en bloc resection",
            "complete piece-meal resection",
            "partial resection",
            "failure",
        }
    assert _labels(mst_3_0, "mst_proc_ercp_stone_extraction_details", "Result") == {
        "complete clearance",
        "partial clearance",
        "questionable",
    }


def test_severity_is_sourced_from_excel(mst_3_0: KnowledgeBase) -> None:
    choices = mst_3_0.classification["mst_event_severity"].classification_choices
    assert [mst_3_0.classification_choice[name].name_en for name in choices] == [
        "Incident",
        "Mild",
        "Moderate",
        "Severe",
        "Fatal",
    ]
    assert (
        "unplanned hospitalization <3 nights"
        in mst_3_0.classification_choice["mst_event_severity_mild"].description
    )
    assert (
        "mst_event_severity"
        in mst_3_0.finding["mst_event_postprocedure_pancreatitis"].classifications
    )


@pytest.mark.parametrize(
    "template,finding",
    [
        ("mst_egd_report", "mst_protruding_polyp"),
        ("mst_colonoscopy_report", "mst_protruding_polyp"),
        ("mst_eus_report", "mst_eus_mass"),
        ("mst_ercp_report", "mst_ercp_tumor"),
    ],
)
def test_reports_expose_all_imported_attributes(
    mst_3_0: KnowledgeBase, template: str, finding: str
) -> None:
    payload = mst_3_0.export_report_template(template)
    fields = [
        f
        for section in payload["report_sections"]
        for f in section["findings"]
        if f["finding"] == finding
    ]
    assert len(fields) == 1
    source = {
        name
        for name in mst_3_0.finding[finding].classifications
        if "mst_location" not in mst_3_0.classification[name].classification_types
    }
    exported = {c["classification"] for c in fields[0]["classifications"]}
    assert source <= exported
    assert len(exported) == len(mst_3_0.finding[finding].classifications)
    if template == "mst_colonoscopy_report":
        locations = [
            mst_3_0.classification[name]
            for name in exported
            if "mst_location" in mst_3_0.classification[name].classification_types
        ]
        assert len(locations) == 1
        assert set(locations[0].classification_choices) == (
            set(mst_3_0.classification["mst_location_colon"].classification_choices)
            | set(mst_3_0.classification["mst_location_ileum"].classification_choices)
        )


def test_import_is_reproducible_and_keeps_existing_identifiers(
    mst_3_0: KnowledgeBase,
) -> None:
    import yaml

    from scripts.import_mst_excel import GENERATED, ImportSpec, render

    outputs = render(
        ROOT, ROOT / "mst30_tables(1).xls", ROOT / "scripts/mst/import.yml"
    )
    assert all(
        (ROOT / path).read_text() == contents for path, contents in outputs.items()
    )
    generated = yaml.safe_load(outputs[GENERATED])
    identities = [(r["model"], r["name"]) for r in generated]
    assert len(identities) == len(set(identities))
    # Shared literals and numeric descriptors are generated once, even when many
    # findings and indications use them.
    numeric = [
        r
        for r in generated
        if r["model"] == "classification_choice_descriptor"
        and r.get("classification_choice_descriptor_type") == "numeric"
        and r["name"].startswith("mst_excel_numeric_")
    ]
    assert len({r["unit"] for r in numeric}) == len(numeric)
    spec = ImportSpec.model_validate(
        yaml.safe_load((ROOT / "scripts/mst/import.yml").read_text())
    )
    names = (
        set(mst_3_0.finding)
        | set(mst_3_0.indication)
        | set(mst_3_0.intervention)
        | set(mst_3_0.classification_choice)
    )
    assert all(
        binding.name in names
        for bindings in spec.bindings.values()
        for binding in bindings.values()
    )


def test_import_rejects_unreviewed_workbook(tmp_path: Path) -> None:
    import yaml

    from scripts.import_mst_excel import ImportSpec, read_workbook

    spec = ImportSpec.model_validate(
        yaml.safe_load((ROOT / "scripts/mst/import.yml").read_text())
    )
    changed = tmp_path / "changed.xls"
    changed.write_bytes((ROOT / "mst30_tables(1).xls").read_bytes() + b"changed")
    with pytest.raises(ValueError, match="SHA-256"):
        read_workbook(changed, spec)
    spec.bindings["Luminal_findings"]["B90"].label = "Wrong expected term"
    with pytest.raises(ValueError, match="expected"):
        read_workbook(ROOT / "mst30_tables(1).xls", spec)


@pytest.mark.parametrize(
    "sheet,start,end,column,groups",
    [
        (
            "Luminal_findings_organ",
            6,
            70,
            2,
            [
                "mst_location_" + organ
                for organ in [
                    "esophagus",
                    "stomach",
                    "duodenum",
                    "jejunum",
                    "ileum",
                    "colon",
                ]
            ],
        ),
        (
            "EUS findings_organ",
            4,
            28,
            1,
            [
                "mst_eus_location_" + organ
                for organ in [
                    "esophagus",
                    "stomach",
                    "duodenum",
                    "pancreas",
                    "biliary_tract",
                    "colorectum",
                ]
            ],
        ),
    ],
)
def test_delivered_locations_match_every_workbook_matrix_row(
    mst_3_0: KnowledgeBase,
    sheet: str,
    start: int,
    end: int,
    column: int,
    groups: list[str],
) -> None:
    import xlrd
    import yaml

    from scripts.import_mst_excel import ImportSpec

    source = xlrd.open_workbook(str(ROOT / "mst30_tables(1).xls")).sheet_by_name(sheet)
    spec = ImportSpec.model_validate(
        yaml.safe_load((ROOT / "scripts/mst/import.yml").read_text())
    )
    for row in range(start, end + 1):
        if not source.cell_value(row - 1, column - 1):
            continue
        owner = spec.bindings[sheet][f"{chr(64 + column)}{row}"].name
        expected = set()
        for offset, group in enumerate(groups, column):
            if source.cell_value(row - 1, offset).lower() == "x":
                expected.update(mst_3_0.classification[group].classification_choices)
        assert (
            set(_classification(mst_3_0, owner, "Location").classification_choices)
            == expected
        )
