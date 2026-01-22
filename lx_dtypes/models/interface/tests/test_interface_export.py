import json
from pathlib import Path

import pytest

from lx_dtypes.models.knowledge_base.main import KB_MODEL_NAMES_ORDERED
from lx_dtypes.utils.parser import camel_to_snake

from ..DbInterface import DbInterface

TEST_INTERFACE_EXPORT_FILE = Path("./test_interface_export.yaml")


class TestKnowledgeBaseDataLoader:
    def test_knowledge_base_data_loader(self) -> None:
        # TODO
        return None

    def test_db_interface_schema(self) -> None:
        _db_interface = DbInterface.create_empty(
            name="TestDBInterface", version="1.0.0"
        )

        # Dump schema
        schema = DbInterface.model_json_schema()
        schema_path = Path("./db_interface_schema.json")
        schema_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")

        assert schema_path.exists()
        assert "knowledge_base" in schema.get("properties", {})
        assert "ledger" in schema.get("properties", {})


class TestDbInterfaceExport:
    def test_db_interface_export(self, db_interface_fixture: "DbInterface") -> None:
        expected_dict = db_interface_fixture.model_dump()

        new_db_interface_instance = DbInterface.model_validate(expected_dict)
        new_dict = new_db_interface_instance.model_dump()

        # Test Dump
        new_db_interface_instance.to_yaml(TEST_INTERFACE_EXPORT_FILE)

        reimported_interface = DbInterface.from_yaml_file(TEST_INTERFACE_EXPORT_FILE)
        re_imported_dict = reimported_interface.model_dump()
        compare_fields = [camel_to_snake(name) for name in KB_MODEL_NAMES_ORDERED]

        for field in compare_fields:
            original_value = expected_dict["knowledge_base"][field]
            new_value_1 = new_dict["knowledge_base"][field]
            new_value_2 = re_imported_dict["knowledge_base"][field]

            assert original_value == new_value_1, (
                f"Mismatch in field {field} after re-validation."
            )
            assert original_value == new_value_2, (
                f"Mismatch in field {field} after YAML export/import."
            )

        assert new_dict == expected_dict


@pytest.mark.django_db
class TestDbInterfaceDjangoExport:
    def test_db_interface_django_export(
        self, db_interface_fixture: "DbInterface"
    ) -> None:
        from lx_dtypes.models.knowledge_base.examination.ExaminationDjango import (
            ExaminationDjango,
        )
        from lx_dtypes.utils.django_sync import sync_django_db_from_interface

        sync_django_db_from_interface(db_interface_fixture)

        COLO_NAME = "colonoscopy"
        POLYP_FINDING_NAME = "colon_polyp"
        INTERVENTION_NAME = "endoscopy_biopsy_grasper_generic"
        CLASSIFICATION_NAME = "lesion_size_mm"
        CLASSIFICATION_CHOICE_NAME = "lesion_size_oval_mm"
        # DESCRIPTOR_NAME =

        colo_exam = ExaminationDjango.objects.get(name=COLO_NAME)
        assert colo_exam.name == COLO_NAME

        # make sure Polyp Finding is linked

        polyp_finding = colo_exam.findings.get(name=POLYP_FINDING_NAME)
        assert polyp_finding.name == POLYP_FINDING_NAME

        intervention = polyp_finding.interventions.get(name=INTERVENTION_NAME)
        assert intervention.name == INTERVENTION_NAME

        classification = polyp_finding.classifications.get(name=CLASSIFICATION_NAME)
        assert classification.name == CLASSIFICATION_NAME

        classification_choice = classification.classification_choices.get(
            name=CLASSIFICATION_CHOICE_NAME
        )
        assert classification_choice.name == CLASSIFICATION_CHOICE_NAME
