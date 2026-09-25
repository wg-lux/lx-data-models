from pathlib import Path

import yaml

from lx_dtypes.models.interface.DataLoader import DataLoader


def test_report_template_export(tmp_path: Path) -> None:
    module_dir = tmp_path / "report_module"
    module_dir.mkdir(parents=True)

    config_path = module_dir / "config.yaml"
    data_path = module_dir / "report_template.yaml"

    config_path.write_text(
        yaml.safe_dump(
            {
                "name": "report_module",
                "version": "1.0.0",
                "modules": [],
                "depends_on": [],
                "data": {
                    "files": ["./report_template.yaml"],
                },
            }
        ),
        encoding="utf-8",
    )

    data_path.write_text(
        yaml.safe_dump(
            [
                {
                    "model": "classification_choice_descriptor",
                    "name": "size_mm_value",
                    "classification_choice_descriptor_type": "numeric",
                    "numeric_min": 0,
                    "numeric_max": 200,
                },
                {
                    "model": "classification_choice",
                    "name": "size_mm",
                    "classification_choice_descriptors": ["size_mm_value"],
                },
                {
                    "model": "classification",
                    "name": "lesion_size",
                    "classification_choices": ["size_mm"],
                },
                {
                    "model": "finding",
                    "name": "esophagus_polyp",
                    "classifications": ["lesion_size"],
                },
                {
                    "model": "examination",
                    "name": "star_upper_gi_endoscopy",
                    "findings": ["esophagus_polyp"],
                },
                {
                    "model": "report_finding",
                    "name": "rf_polyp",
                    "finding": "esophagus_polyp",
                    "required": False,
                    "multiple_allowed": True,
                    "classifications": [
                        {
                            "classification": "lesion_size",
                            "required": True,
                        }
                    ],
                },
                {
                    "model": "report_template_section",
                    "name": "examination_baseline",
                    "position": 0,
                    "types": [],
                    "findings": [
                        {
                            "finding": "esophagus_polyp",
                            "required": False,
                            "multiple_allowed": True,
                            "classifications": [
                                {
                                    "classification": "lesion_size",
                                    "required": True,
                                }
                            ],
                        },
                        "rf_polyp",
                    ],
                },
                {
                    "model": "findings_validator",
                    "name": "polyp_has_lst_if_large",
                    "query": {
                        "finding": "esophagus_polyp",
                        "operator": "exists",
                    },
                },
                {
                    "model": "examination_validator",
                    "name": "gastroscopy_has_baseline_info",
                    "finding_validators": [
                        "star_upper_gi_mucosa_esophagus_abnormal_reported",
                    ],
                    "examination_validators": [],
                },
                {
                    "model": "report_template",
                    "name": "star_upper_gi_main",
                    "version": "1.0.0",
                    "coverage_version": "report_concept_coverage_v1",
                    "coverage_concepts": [
                        {
                            "concept_id": "upper_gi.polyp",
                            "label": "Polyp",
                            "applicability_status": "required",
                            "validator_names": ["polyp_has_lst_if_large"],
                            "evidence_path": ["patient_findings"],
                            "finding_selector": {
                                "finding_name": "esophagus_polyp",
                            },
                            "concept_value_path": ["finding"],
                            "allowed_values": ["esophagus_polyp"],
                        }
                    ],
                    "examination": "star_upper_gi_endoscopy",
                    "report_sections": ["examination_baseline"],
                    "validators": {
                        "examination_validators": ["gastroscopy_has_baseline_info"],
                        "findings_validators": ["polyp_has_lst_if_large"],
                    },
                },
            ],
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    loader = DataLoader(input_dirs=[tmp_path])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("report_module")

    exported = kb.export_report_template("star_upper_gi_main")

    assert exported["name"] == "star_upper_gi_main"
    assert exported["version"] == "1.0.0"
    assert exported["coverage_version"] == "report_concept_coverage_v1"
    assert exported["coverage_concepts"][0]["concept_id"] == "upper_gi.polyp"
    assert exported["examination"] == "star_upper_gi_endoscopy"
    assert len(exported["report_sections"]) == 1

    section = exported["report_sections"][0]
    assert section["name"] == "examination_baseline"
    assert len(section["findings"]) == 2

    assert section["findings"][0]["finding"] == "esophagus_polyp"
    assert section["findings"][1]["finding"] == "esophagus_polyp"
    descriptor_input = section["findings"][1]["classifications"][0]["input"]["choices"][
        0
    ]["descriptors"][0]
    assert descriptor_input["name"] == "size_mm_value"
    assert descriptor_input["type"] == "numeric"
    assert descriptor_input["numeric_min"] == 0
    assert descriptor_input["numeric_max"] == 200

    resolved_exam_validators = exported["validators"]["examination_validators"]
    resolved_classification_validators = exported["validators"][
        "classification_validators"
    ]
    resolved_findings_validators = exported["validators"]["findings_validators"]

    assert isinstance(resolved_exam_validators[0], dict)
    assert resolved_exam_validators[0]["name"] == "gastroscopy_has_baseline_info"
    assert resolved_classification_validators == []
    assert isinstance(resolved_findings_validators[0], dict)
    assert resolved_findings_validators[0]["name"] == "polyp_has_lst_if_large"
