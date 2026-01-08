from pathlib import Path

from ..DbInterface import DbInterface

TEST_INTERFACE_EXPORT_FILE = Path("./test_interface_export.yaml")
from lx_dtypes.models.knowledge_base.main import KB_MODEL_NAMES_ORDERED
from lx_dtypes.utils.parser import camel_to_snake


class TestKnowledgeBaseDataLoader:
    def test_knowledge_base_data_loader(self) -> None:
        # TODO
        return None


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

            assert (
                original_value == new_value_1
            ), f"Mismatch in field {field} after re-validation."
            assert (
                original_value == new_value_2
            ), f"Mismatch in field {field} after YAML export/import."

        assert new_dict == expected_dict
