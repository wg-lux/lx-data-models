import json
from pathlib import Path

import pytest

from lx_dtypes.models.knowledge_base.main import KB_MODEL_NAMES_ORDERED
from lx_dtypes.utils.parser import camel_to_snake

from lx_dtypes.models.interface.DbInterface import DbInterface


class TestKnowledgeBaseDataLoader:
    def test_knowledge_base_data_loader(self) -> None:
        # TODO
        return None

    def test_db_interface_schema(self, tmp_path: Path) -> None:
        """
        Create an empty DbInterface, export its JSON schema to ./db_interface_schema.json, and verify required properties.

        Verifies that the schema file is created and that the schema's top-level properties include "knowledge_base" and "ledger".
        """
        DbInterface.create_empty(name="TestDBInterface", version="1.0.0")

        # Dump schema
        schema = DbInterface.model_json_schema()
        schema_path = tmp_path / "db_interface_schema.json"
        schema_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")

        assert schema_path.exists()
        assert "knowledge_base" in schema.get("properties", {})
        assert "ledger" in schema.get("properties", {})


class TestDbInterfaceExport:
    def test_db_interface_export(
        self, db_interface_fixture: "DbInterface", tmp_path: Path
    ) -> None:
        """
        Validate that a DbInterface instance round-trips through model validation and YAML export/import without loss.

        This test:
        - Dumps the provided DbInterface fixture to a dict.
        - Re-validates that dict via DbInterface.model_validate() and re-dumps it.
        - Exports the re-validated instance to YAML and re-imports it from that file.
        - Compares each knowledge_base field (mapped from KB_MODEL_NAMES_ORDERED to snake_case) between the original, the re-validated, and the YAML re-imported representations and asserts equality.
        - Asserts the full re-validated dict equals the original dumped dict.

        Parameters:
            db_interface_fixture (DbInterface): A pre-built DbInterface instance used as the source for validation and export/import checks.
        """
        expected_dict = db_interface_fixture.model_dump()

        new_db_interface_instance = DbInterface.model_validate(expected_dict)
        new_dict = new_db_interface_instance.model_dump()

        # Test Dump
        export_path = tmp_path / "db_interface_export.yaml"
        new_db_interface_instance.to_yaml(export_path)

        reimported_interface = DbInterface.from_yaml_file(export_path)
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
        """
        Sync the provided DbInterface into the Django database and verify key knowledge-base entities exist.

        This test synchronizes the given DbInterface to the Django ORM and asserts that a colonoscopy examination and its related
        knowledge-base objects are present and correctly linked: the "colonoscopy" examination, the "colon_polyp" finding,
        the "endoscopy_biopsy_grasper_generic" intervention, the "lesion_size_mm" classification, and the "lesion_size_oval_mm"
        classification choice.
        Parameters:
            db_interface_fixture (DbInterface): A populated DbInterface instance to be synchronized into Django.
        """
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
