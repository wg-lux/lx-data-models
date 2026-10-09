from pathlib import Path

import pytest
from pydantic import ValidationError

from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.interface.KnowledgeBaseResolver import load_knowledge_base
from lx_dtypes.models.knowledge_base.center.center_employee_list import (
    CenterEmployeeList,
)
from lx_dtypes.models.knowledge_base.study_preset import StudyPreset
from lx_dtypes.models.ledger.examiner.Pydantic import Examiner


def test_standard_package_loads_existing_examiner_contract(tmp_path: Path) -> None:
    module = tmp_path / "employees"
    module.mkdir()
    (module / "config.yaml").write_text(
        "name: employees\nversion: 1.0.0\ndata:\n  files: [staff.yml]\n"
    )
    (module / "staff.yml").write_text(
        "- model: study_preset\n  name: local_setup\n"
        "  centers:\n    - name: clinic\n"
        "  genders:\n    - name: unknown\n"
        "  labels:\n    - name: low_quality\n"
        "- model: center_employee_list\n  name: local_staff\n  examiners:\n"
        "    - center: clinic\n      first_name: Test\n      last_name: Employee\n"
    )
    kb = load_knowledge_base("employees", version="1.0.0", input_dirs=[tmp_path])
    assert isinstance(kb, KnowledgeBase)
    assert kb.study_preset["local_setup"].centers[0].name == "clinic"
    assert kb.study_preset["local_setup"].genders[0].name == "unknown"
    roster = kb.center_employee_list["local_staff"]
    assert isinstance(roster.examiners[0], Examiner)
    assert roster.examiners[0].center == "clinic"
    assert (
        CenterEmployeeList.model_validate(roster.model_dump()).examiners[0].first_name
        == "Test"
    )
    assert (
        kb.ddict["center_employee_list"]["local_staff"]["examiners"][0]["last_name"]
        == "Employee"
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("center", ""),
        ("first_name", " "),
        ("last_name", "unknown"),
        ("last_name", 42),
        ("first_name", "a" * 256),
    ],
)
def test_employee_package_rejects_invalid_recognition_values(
    field: str, value: object
) -> None:
    employee: dict[str, object] = {
        "center": "clinic",
        "first_name": "Test",
        "last_name": "Employee",
    }
    employee[field] = value
    with pytest.raises(ValidationError):
        CenterEmployeeList.model_validate({"name": "staff", "examiners": [employee]})


def test_employee_package_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        CenterEmployeeList.model_validate(
            {
                "name": "staff",
                "examiners": [
                    {
                        "center": "clinic",
                        "first_name": "Test",
                        "last_name": "Employee",
                        "typo": True,
                    }
                ],
            }
        )


def test_label_set_version_is_required_and_part_of_identity() -> None:
    with pytest.raises(ValidationError):
        StudyPreset.model_validate(
            {"name": "setup", "label_sets": [{"name": "review"}]}
        )
    preset = StudyPreset.model_validate(
        {
            "name": "setup",
            "label_sets": [
                {"name": "review", "version": 1},
                {"name": "review", "version": 2},
            ],
        }
    )
    assert [row.version for row in preset.label_sets] == [1, 2]
    assert preset.ddict["label_sets"][0]["version"] == 1


@pytest.mark.parametrize(
    "payload",
    [
        {"centers": [{}]},
        {"labels": [{"name": ""}]},
        {"genders": [{"name": "unknown"}, {"name": "unknown"}]},
        {
            "label_sets": [
                {"name": "review", "version": 1},
                {"name": "review", "version": 1},
            ]
        },
    ],
)
def test_invalid_preset_records_fail_validation(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        StudyPreset.model_validate({"name": "setup", **payload})
