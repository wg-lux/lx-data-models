from pathlib import Path

from lx_dtypes.models.interface.DataLoader import DataLoader


DATA_ROOT = Path(__file__).resolve().parents[3] / "data"


def test_knowledge_base_runtime_execution_for_example_template() -> None:
    loader = DataLoader(input_dirs=[DATA_ROOT])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("report_template_examples")

    failing = kb.evaluate_report_template_validators(
        "star_upper_gi_main",
        reported_findings=[
            {
                "finding": "star_upper_gi_mucosa_esophagus_abnormal",
                "classifications": [],
            },
            {
                "finding": "esophagus_polyp",
                "classifications": [
                    {"classification": "size_mm", "value": 12},
                ],
            },
        ],
    )
    passing = kb.evaluate_report_template_validators(
        "star_upper_gi_main",
        reported_findings=[
            {
                "finding": "star_upper_gi_mucosa_esophagus_abnormal",
                "classifications": [],
            },
            {
                "finding": "esophagus_polyp",
                "classifications": [
                    {"classification": "size_mm", "value": 12},
                    {"classification": "lst", "value": "present"},
                ],
            },
        ],
    )

    assert failing["ok"] is False
    assert any(
        issue["code"] == "missing_required_classification"
        for issue in failing["issues"]
    )
    assert passing["ok"] is True


def test_knowledge_base_runtime_execution_flags_missing_exam_requirement() -> None:
    loader = DataLoader(input_dirs=[DATA_ROOT])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("report_template_examples")

    result = kb.evaluate_report_template_validators(
        "star_upper_gi_main",
        reported_findings=[
            {
                "finding": "esophagus_polyp",
                "classifications": [
                    {"classification": "size_mm", "value": 8},
                ],
            }
        ],
    )

    assert result["ok"] is False
    exam_results = result["examination_validators"]
    assert exam_results
    assert exam_results[0]["ok"] is False
