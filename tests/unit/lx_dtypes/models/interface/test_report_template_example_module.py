import datetime
import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.models.knowledge_base.report_template.ReportTemplate import (
    ReportTemplate,
    ReportTemplateGuidelineReference,
)
from lx_dtypes.models.knowledge_base.report_template.ReportTemplateGraph import (
    validate_report_template_structure,
)


def test_report_template_example_module_yaml_json_roundtrip() -> None:
    loader = DataLoader(input_dirs=[Path("./lx_dtypes/data/")])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("report_template_examples")

    exported = kb.export_report_template_preview("star_upper_gi_main")

    exported_json = json.dumps(exported, sort_keys=True, default=str)
    exported_back = json.loads(exported_json)

    assert exported_back["name"] == "star_upper_gi_main"
    assert exported_back["examination"] == "star_upper_gi_endoscopy"
    assert len(exported_back["report_sections"]) == 1
    assert exported_back["readiness"]["can_preview"] is True

    template = kb.get_report_template("star_upper_gi_main")
    template_json = template.model_dump_json()
    template_back = ReportTemplate.model_validate_json(template_json)

    assert template_back.model_dump() == template.model_dump()

    assert exported_back["validators"]["findings_validators"][0]["name"] == (
        "polyp_has_lst_if_large"
    )
    assert exported_back["validators"]["examination_validators"][0]["name"] == (
        "gastroscopy_has_baseline_info"
    )


def test_report_template_guideline_reference_rejects_non_https_source() -> None:
    with pytest.raises(ValidationError, match="must use HTTPS"):
        ReportTemplateGuidelineReference(
            guideline_id="AWMF-021-022",
            title="Quality guideline",
            issuing_organization="DGVS",
            version="2.1",
            publication_date=datetime.date(2025, 7, 1),
            canonical_url="http://example.test/guideline.pdf",
            cited_sections=["Statement 2.36"],
        )


def test_upper_gi_quality_2025_is_localized_guideline_backed_and_publishable() -> None:
    loader = DataLoader(input_dirs=[Path("./lx_dtypes/data/")])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("report_template_examples")

    exported = kb.export_report_template("upper_gi_quality_2025")

    assert exported["readiness"]["can_publish"] is True
    assert exported["examination"] == "star_upper_gi_endoscopy"
    assert exported["name_de"].startswith("ÖGD")
    assert exported["version"] == "ESGE-upper-GI-2025"
    assert {
        reference["guideline_id"] for reference in exported["guideline_references"]
    } == {"ESGE-UGI-PM-2025", "ESGE-STAR-UGI-2025", "AWMF-021-022"}
    assert len(exported["coverage_concepts"]) == 7


@pytest.mark.parametrize(
    ("template_name", "examination", "concept_count", "guideline_id"),
    [
        ("ercp_quality_2018", "ercp", 5, "ESGE-ERCP-EUS-PM-2018"),
        (
            "eus_quality_2025",
            "endoscopic_ultrasound",
            5,
            "ESGE-EUS-PM-2025",
        ),
    ],
)
def test_advanced_endoscopy_templates_are_guideline_backed_and_publishable(
    template_name: str,
    examination: str,
    concept_count: int,
    guideline_id: str,
) -> None:
    loader = DataLoader(input_dirs=[Path("./lx_dtypes/data/")])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("report_template_examples")

    exported = kb.export_report_template(template_name)

    assert exported["readiness"]["can_publish"] is True
    assert exported["examination"] == examination
    assert len(exported["coverage_concepts"]) == concept_count
    assert guideline_id in {
        reference["guideline_id"] for reference in exported["guideline_references"]
    }
    assert all(
        concept["guideline_citations"] for concept in exported["coverage_concepts"]
    )


def test_colonoscopy_template_covers_guideline_report_documentation() -> None:
    loader = DataLoader(input_dirs=[Path("./lx_dtypes/data/")])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("report_template_examples")

    exported = kb.export_report_template("colonoscopy_training_basic")
    sections = {section["name"]: section for section in exported["report_sections"]}

    assert exported["readiness"]["can_publish"] is True
    assert exported["name_de"] == (
        "Koloskopie – leitlinienbasierte Qualitätsdokumentation"
    )
    assert exported["name_en"] == (
        "Colonoscopy – guideline-based quality documentation"
    )
    assert exported["version"] == "DGVS-AWMF-021-022-v2.1-2025-07"
    assert {
        reference["guideline_id"] for reference in exported["guideline_references"]
    } == {"AWMF-021-022", "AWMF-021-014"}
    assert all(
        reference["canonical_url"].startswith("https://")
        for reference in exported["guideline_references"]
    )
    assert "Statement 2.36" in exported["guideline_references"][0]["cited_sections"]
    assert exported["coverage_version"] == "report_concept_coverage_v1"
    assert {concept["concept_id"] for concept in exported["coverage_concepts"]} == {
        "koloskopie.patientenidentitaet",
        "koloskopie.indikation",
        "koloskopie.untersuchende",
        "koloskopie.assistenzbereitschaft",
        "koloskopie.geraet.modell",
        "koloskopie.geraet.seriennummer",
        "koloskopie.prozesszeit.raum_betreten",
        "koloskopie.prozesszeit.endoskop_eingefuehrt",
        "koloskopie.prozesszeit.rueckzug_begonnen",
        "koloskopie.prozesszeit.endoskop_entfernt",
        "koloskopie.prozesszeit.raum_verlassen",
        "koloskopie.prozesszeit.abteilung_verlassen",
        "koloskopie.monitoring.zeitpunkt",
        "koloskopie.monitoring.herzfrequenz",
        "koloskopie.monitoring.blutdruck_systolisch",
        "koloskopie.monitoring.blutdruck_diastolisch",
        "koloskopie.monitoring.sauerstoffsaettigung",
        "koloskopie.bbps.gesamtwert",
        "koloskopie.zoekum_landmarken.appendixostium_bildreferenz",
        "koloskopie.zoekum_landmarken.ileozoekalklappe_bildreferenz",
        "koloskopie.pathologiestatus",
        "koloskopie.nachsorgeempfehlung",
        "koloskopie.sedierungsstatus",
        "koloskopie.medikationsstatus",
        "koloskopie.bbps.linkes_kolon",
        "koloskopie.bbps.transversum",
        "koloskopie.bbps.rechtes_kolon",
        "koloskopie.maximale_reichweite",
        "koloskopie.rueckzugszeit_feld",
        "koloskopie.zoekum_landmarken.appendixostium",
        "koloskopie.zoekum_landmarken.ileozoekalklappe",
        "koloskopie.technik.hd_videoendoskop",
        "koloskopie.technik.co2_insufflation",
        "koloskopie.komplikationsstatus",
    }
    assert all(
        concept["guideline_citations"] for concept in exported["coverage_concepts"]
    )
    assert list(sections) == [
        "patienten_und_untersuchungskontext",
        "indikation_und_sedierung",
        "darmvorbereitung_nach_bbps",
        "untersuchungsqualitaet_und_reichweite",
        "pathologische_befunde_und_interventionen",
        "komplikationen_und_empfehlungen",
    ]
    assert {
        section_name: section["title_de"] for section_name, section in sections.items()
    } == {
        "patienten_und_untersuchungskontext": "Patienten- und Untersuchungskontext",
        "indikation_und_sedierung": "Indikation und Sedierung",
        "darmvorbereitung_nach_bbps": "Darmvorbereitung nach BBPS",
        "untersuchungsqualitaet_und_reichweite": (
            "Untersuchungsqualität und Reichweite"
        ),
        "pathologische_befunde_und_interventionen": (
            "Pathologische Befunde und Interventionen"
        ),
        "komplikationen_und_empfehlungen": "Komplikationen und Empfehlungen",
    }
    assert all(section["title_en"] for section in sections.values())

    required_findings = {
        finding["finding"]
        for section in exported["report_sections"]
        for finding in section["findings"]
        if finding["required"]
    }
    assert required_findings == {
        "endoscopy_hardware_used",
        "sedation_endoscopy",
        "endoscopy_medication_status",
        "endoscopy_process_timestamps",
        "endoscopy_preprocedure_team_timeout",
        "endoscopy_postprocedure_sign_out",
        "endoscopy_preprocedure_risk_assessment_checklist",
        "bowel_preparation_lc",
        "bowel_preparation_tc",
        "bowel_preparation_rc",
        "bowel_preparation_bbps_total",
        "colonoscopy_deepest_viewed_location",
        "colonoscopy_withdrawal_time_minutes",
        "colonoscopy_cecal_landmarks_photodocumented",
        "colonoscopy_technical_quality",
        "colonoscopy_complication_status",
        "colonoscopy_pathology_summary",
        "colonoscopy_follow_up_plan",
    }
    context_fields = sections["patienten_und_untersuchungskontext"]["fields"]
    assert {field["key"] for field in context_fields} >= {
        "indication",
        "examiner",
        "assisting_personnel",
        "device_identification",
        "relevant_images",
    }

    process_timing = next(
        finding
        for finding in sections["untersuchungsqualitaet_und_reichweite"]["findings"]
        if finding["finding"] == "endoscopy_process_timestamps"
    )
    assert process_timing["required"] is True
    assert {
        classification["classification"]
        for classification in process_timing["classifications"]
    } == {
        "endoscopy_room_entry_time",
        "endoscope_insertion_time",
        "colonoscopy_withdrawal_start_time",
        "endoscope_removal_time",
        "endoscopy_room_exit_time",
        "endoscopy_department_exit_time",
    }

    sedation_findings = {
        finding["finding"]
        for finding in sections["indikation_und_sedierung"]["findings"]
    }
    assert {
        "endoscopy_sedation_monitoring_measurement",
        "endoscopy_supplemental_oxygen_administration",
        "endoscopy_intravenous_fluid_status",
        "endoscopy_intravenous_fluid_administration",
        "endoscopy_post_sedation_recovery_assessment",
        "endoscopy_post_sedation_discharge_or_transfer_assessment",
    } <= sedation_findings
    medication_finding = next(
        finding
        for finding in sections["indikation_und_sedierung"]["findings"]
        if finding["finding"] == "endoscopy_medication_administration"
    )
    assert medication_finding["multiple_allowed"] is True
    product_requirement = next(
        classification
        for classification in medication_finding["classifications"]
        if classification["classification"] == "endoscopy_medication_product_and_dose"
    )
    propofol_input = next(
        choice
        for choice in product_requirement["input"]["choices"]
        if choice["name"] == "medication_propofol"
    )
    assert propofol_input["descriptors"][0]["name"] == "propofol_dose_mg_value"
    assert propofol_input["descriptors"][0]["unit_abbreviation"] == "mg"
    method_requirement = next(
        classification
        for classification in medication_finding["classifications"]
        if classification["classification"] == "medication_administration_method"
    )
    infusion_input = next(
        choice
        for choice in method_requirement["input"]["choices"]
        if choice["name"] == "medication_method_infusion"
    )
    assert infusion_input["descriptors"][0]["name"] == (
        "medication_infusion_volumetric_flow_rate_value"
    )
    assert infusion_input["descriptors"][0]["unit_abbreviation"] == "ml/h"

    validators = exported["validators"]["examination_validators"]
    assert validators[0]["name"] == "koloskopie_mindestdokumentation"
    assert (
        "koloskopie_rueckzugszeit_dokumentiert" in validators[0]["finding_validators"]
    )
    assert (
        "koloskopie_inkomplettheitsgrund_erforderlich"
        in validators[0]["finding_validators"]
    )
    assert (
        "koloskopie_inadaequate_vorbereitung_fruehe_wiederholung"
        in validators[0]["finding_validators"]
    )


@pytest.fixture(params=["kb_alias", "inline"])
def report_template_module(tmp_path: Path, request: pytest.FixtureRequest) -> Path:
    mode = request.param
    module_dir = tmp_path / f"rt_{mode}"
    module_dir.mkdir(parents=True)

    (module_dir / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "name": f"rt_{mode}",
                "version": "1.0.0",
                "modules": [],
                "depends_on": [],
                "data": {"files": ["./report_template.yaml"]},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    records = [
        {"model": "finding", "name": "esophagus_polyp"},
        {
            "model": "examination",
            "name": "star_upper_gi_endoscopy",
            "findings": ["esophagus_polyp"],
        },
    ]

    section_findings: list[str] | list[dict[str, Any]]
    if mode == "kb_alias":
        records.append(
            {
                "model": "report_finding",
                "name": "rf_polyp",
                "finding": "esophagus_polyp",
                "required": True,
                "multiple_allowed": False,
                "classifications": [],
            }
        )
        section_findings = ["rf_polyp"]
    else:
        section_findings = [
            {
                "finding": "esophagus_polyp",
                "required": True,
                "multiple_allowed": False,
                "classifications": [],
            }
        ]

    records.extend(
        [
            {
                "model": "report_template_section",
                "name": "baseline",
                "position": 0,
                "types": ["baseline"],
                "findings": section_findings,
            },
            {
                "model": "report_template",
                "name": "test_template",
                "examination": "star_upper_gi_endoscopy",
                "report_sections": ["baseline"],
                "validators": {
                    "examination_validators": [],
                    "findings_validators": [],
                },
            },
        ]
    )

    (module_dir / "report_template.yaml").write_text(
        yaml.safe_dump(records, sort_keys=False),
        encoding="utf-8",
    )
    return module_dir


def test_report_template_validator_inline_vs_kb_alias_parity(
    report_template_module: Path,
) -> None:
    loader = DataLoader(input_dirs=[report_template_module.parent])
    loader.load_module_configs()
    kb = loader.load_knowledge_base(report_template_module.name)

    template = kb.get_report_template("test_template")
    result = validate_report_template_structure(
        template,
        sections=kb.report_template_section,
        report_findings=kb.report_finding,
        findings=kb.finding,
    )

    assert result.ok is True
    assert not [issue for issue in result.issues if issue.level == "error"]

    graph = result.graph
    finding_nodes = [n for n in graph.nodes if n.node_type == "finding"]
    section_nodes = [n for n in graph.nodes if n.node_type == "section"]

    assert len(section_nodes) == 1
    assert section_nodes[0].name == "baseline"
    assert len(finding_nodes) == 1
    assert finding_nodes[0].name == "esophagus_polyp"


def test_report_template_validator_broken_alias_surfaces_warning(
    tmp_path: Path,
) -> None:
    module_dir = tmp_path / "rt_broken_alias"
    module_dir.mkdir(parents=True)
    (module_dir / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "name": "rt_broken_alias",
                "version": "1.0.0",
                "modules": [],
                "depends_on": [],
                "data": {"files": ["./report_template.yaml"]},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (module_dir / "report_template.yaml").write_text(
        yaml.safe_dump(
            [
                {"model": "finding", "name": "esophagus_polyp"},
                {
                    "model": "examination",
                    "name": "star_upper_gi_endoscopy",
                    "findings": ["esophagus_polyp"],
                },
                {
                    "model": "report_template_section",
                    "name": "baseline",
                    "position": 0,
                    "types": [],
                    "findings": ["missing_rf_alias"],
                },
                {
                    "model": "report_template",
                    "name": "test_template",
                    "examination": "star_upper_gi_endoscopy",
                    "report_sections": ["baseline"],
                    "validators": {
                        "examination_validators": [],
                        "findings_validators": [],
                    },
                },
            ],
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    loader = DataLoader(input_dirs=[module_dir.parent])
    loader.load_module_configs()
    kb = loader.load_knowledge_base(module_dir.name)
    template = kb.get_report_template("test_template")
    result = validate_report_template_structure(
        template,
        sections=kb.report_template_section,
        report_findings=kb.report_finding,
        findings=kb.finding,
    )

    assert result.ok is True
    assert any(issue.code == "unknown_finding_reference" for issue in result.issues)
