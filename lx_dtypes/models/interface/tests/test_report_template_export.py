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
                    "model": "classification_choice",
                    "name": "size_mm",
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
    assert exported["examination"] == "star_upper_gi_endoscopy"
    assert len(exported["report_sections"]) == 1

    section = exported["report_sections"][0]
    assert section["name"] == "examination_baseline"
    assert len(section["findings"]) == 2

    assert section["findings"][0]["finding"] == "esophagus_polyp"
    assert section["findings"][1]["finding"] == "esophagus_polyp"

    resolved_exam_validators = exported["validators"]["examination_validators"]
    resolved_findings_validators = exported["validators"]["findings_validators"]

    assert isinstance(resolved_exam_validators[0], dict)
    assert resolved_exam_validators[0]["name"] == "gastroscopy_has_baseline_info"
    assert isinstance(resolved_findings_validators[0], dict)
    assert resolved_findings_validators[0]["name"] == "polyp_has_lst_if_large"
