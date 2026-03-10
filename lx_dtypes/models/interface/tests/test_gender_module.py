from pathlib import Path

import pytest

from lx_dtypes.models.interface.DataLoader import DataLoader


@pytest.mark.django_db
def test_gender_data_module_loads_via_dataloader() -> None:
    loader = DataLoader(input_dirs=[Path("./lx_dtypes/data/")])
    loader.load_module_configs()

    kb = loader.load_knowledge_base("gender_data")

    assert "male" in kb.gender
    gender = kb.gender["male"]
    assert gender.name == "male"
    assert gender.abbreviation == "M"
    assert gender.kb_module_name == "gender_data"

    exported = kb.export_record_lists()
    assert any(entry["name"] == "male" for entry in exported["genders"])
