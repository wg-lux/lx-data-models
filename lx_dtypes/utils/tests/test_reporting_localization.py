from pathlib import Path

import yaml

from lx_dtypes.models.interface.DataLoader import DataLoader


TERMINOLOGY_ROOT = Path(__file__).resolve().parents[2] / "data" / "terminology"


def _records(relative_path: str) -> list[dict[str, object]]:
    payload: object = yaml.safe_load(
        (TERMINOLOGY_ROOT / relative_path).read_text(encoding="utf-8")
    )
    assert isinstance(payload, list)
    records: list[dict[str, object]] = []
    for raw_record in payload:
        assert isinstance(raw_record, dict)
        record: dict[str, object] = {}
        for key, value in raw_record.items():
            assert isinstance(key, str)
            record[key] = value
        records.append(record)
    return records


def _assert_localized(record: dict[str, object]) -> None:
    stable_name = record.get("name")
    assert isinstance(stable_name, str) and stable_name
    for field in ("name_de", "name_en"):
        localized_name = record.get(field)
        assert isinstance(localized_name, str) and localized_name.strip(), (
            f"{stable_name} requires a non-empty {field}"
        )
        assert localized_name != stable_name, (
            f"{stable_name} must not expose its stable key as {field}"
        )


def test_colonoscopy_reporting_entry_terms_are_canonically_localized() -> None:
    examinations = _records("lx_examinations/data/colonoscopy.yaml")
    colonoscopy = next(
        record
        for record in examinations
        if record.get("model") == "examination" and record.get("name") == "colonoscopy"
    )
    _assert_localized(colonoscopy)
    assert colonoscopy["name_de"] == "Koloskopie"
    assert colonoscopy["name_en"] == "Colonoscopy"

    indications = {
        name: record
        for record in _records("lx_indications/data/colonoscopy_indications.yaml")
        if record.get("model") == "indication"
        and isinstance(name := record.get("name"), str)
    }
    examination_indications = colonoscopy["indications"]
    assert isinstance(examination_indications, list)
    assert set(indications) == set(examination_indications)
    for indication in indications.values():
        _assert_localized(indication)

    descriptors = _records("lx_descriptors/data/time.yaml")
    minutes = next(
        record
        for record in descriptors
        if record.get("model") == "classification_choice_descriptor"
        and record.get("name") == "minutes_numeric_value"
    )
    _assert_localized(minutes)
    assert minutes["name_de"] == "Zeitwert (Minuten)"
    assert minutes["name_en"] == "Time value (minutes)"


def test_colonoscopy_reporting_localization_survives_knowledge_base_loading() -> None:
    loader = DataLoader(input_dirs=[Path("./lx_dtypes/data/")])
    loader.load_module_configs()
    knowledge_base = loader.load_knowledge_base("report_template_examples")

    colonoscopy = knowledge_base.examination["colonoscopy"]
    assert colonoscopy.name_de == "Koloskopie"
    assert colonoscopy.name_en == "Colonoscopy"

    for indication_name in colonoscopy.indications:
        indication = knowledge_base.indication[indication_name]
        assert indication.name_de and indication.name_de != indication.name
        assert indication.name_en and indication.name_en != indication.name

    minutes = knowledge_base.classification_choice_descriptor["minutes_numeric_value"]
    assert minutes.name_de == "Zeitwert (Minuten)"
    assert minutes.name_en == "Time value (minutes)"
