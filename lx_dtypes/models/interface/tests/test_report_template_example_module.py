import json
from pathlib import Path

from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.models.knowledge_base.report_template.ReportTemplate import ReportTemplate


def test_report_template_example_module_yaml_json_roundtrip() -> None:
    loader = DataLoader(input_dirs=[Path("./lx_dtypes/data/")])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("report_template_examples")

    exported = kb.export_report_template("star_upper_gi_main")

    exported_json = json.dumps(exported, sort_keys=True)
    exported_back = json.loads(exported_json)

    assert exported_back["name"] == "star_upper_gi_main"
    assert exported_back["examination"] == "star_upper_gi_endoscopy"
    assert len(exported_back["report_sections"]) == 2

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
